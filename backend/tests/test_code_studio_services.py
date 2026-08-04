"""Service-layer tests for code_studio, chat, and agent tooling.

Each test drives a real service against FakeSession with a stubbed
ai_service, covering happy paths, AI JSON fallbacks, and failure
branches (missing projects, invalid JSON, ownership checks).
"""
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import NotFoundError
from app.models.agent_network import AgentPerformance, AgentReview
from app.models.chat import ChatSession
from app.models.code_studio import (
    BuildRecord,
    BranchRecord,
    CommitRecord,
    Repository,
    SecurityScan,
    StudioDeployment,
    StudioDocumentation,
    StudioFile,
    StudioProject,
    TestRun,
)
from app.models.agent_network import AgentMessage
from app.services.agent_communication import AgentCommunicationService
from app.services.agent_evaluation import AgentEvaluationService
from app.services.app_generator import AppGeneratorService
from app.services.chat_service import ChatService
from app.services.code_debugger import CodeDebuggerService
from app.services.deployment_manager import DeploymentManagerService
from app.services.doc_generator import DocGeneratorService
from app.services.git_manager import GitManagerService
from app.services.security_scanner import SecurityScannerService
from app.services.test_engine import TestEngineService
from app.schemas.chat import ChatMessageSendRequest


def _project(db, name="Demo App"):
    proj = StudioProject(
        id=uuid.uuid4(), name=name, description="A demo",
        project_type="web", language="python",
        backend_framework="fastapi", frontend_framework="react",
        database_type="postgresql",
    )
    db.add(proj)
    return proj


def _mock_complete(content: str, tokens: int = 0):
    return patch(
        "app.services.ai_service.ai_service.complete",
        AsyncMock(return_value={"content": content, "tokens_used": tokens}),
    )


# ═══════════════════════════════════════════════════════════════════════════
# TEST ENGINE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_tests_happy_path(stateful_client):
    _client, db = stateful_client
    proj = _project(db, "Payments Api")
    db.add(StudioFile(path="app/main.py", name="main.py", content="def x(): pass",
                      language="python", size=16, project_id=proj.id))

    code = "```python\nimport pytest\n\ndef test_x():\n    assert True\n```"
    with _mock_complete(code):
        run = await TestEngineService(db).generate_tests(proj.id, test_type="unit", user_id=uuid.uuid4())

    assert run.test_type == "unit"
    assert run.status == "completed"
    assert run.framework == "pytest"
    assert run.failed == 0
    assert "payments_api" in run.results[0]["file"]
    assert db.objects_of(TestRun)  # persisted


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_tests_missing_project(stateful_client):
    _client, db = stateful_client
    with pytest.raises(ValueError, match="Project not found"):
        await TestEngineService(db).generate_tests(uuid.uuid4())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_tests_filters_files(stateful_client):
    _client, db = stateful_client
    proj = _project(db)
    db.add(StudioFile(path="a.py", name="a.py", content="x", language="python",
                      size=1, project_id=proj.id))
    db.add(StudioFile(path="b.py", name="b.py", content="y", language="python",
                      size=1, project_id=proj.id))
    with _mock_complete("```python\ndef test():\n    pass\n```"):
        run = await TestEngineService(db).generate_tests(
            proj.id, files_to_test=["b.py"])
    assert run.results


# ═══════════════════════════════════════════════════════════════════════════
# CODE DEBUGGER
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_debug_parses_json(stateful_client):
    _client, db = stateful_client
    payload = {"root_cause": "null deref", "solution": "check for None",
               "fixed_code": "x = 1", "suggestions": ["use a guard"]}
    with _mock_complete(json.dumps(payload)):
        result = await CodeDebuggerService(db).debug(code="x = None.x", error_message="AttributeError")
    assert result["root_cause"] == "null deref"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_debug_falls_back_on_bad_json(stateful_client):
    _client, db = stateful_client
    with _mock_complete("not json at all"):
        result = await CodeDebuggerService(db).debug(code="x = 1")
    assert result["root_cause"] == "Analysis completed"
    assert result["fixed_code"] == "x = 1"
    assert len(result["suggestions"]) >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_review_code_json_and_fallback(stateful_client):
    _client, db = stateful_client
    with _mock_complete(json.dumps({"issues": [{"severity": "high"}]})):
        result = await CodeDebuggerService(db).review_code("bad code")
    assert result["issues"][0]["severity"] == "high"

    with _mock_complete("plain prose"):
        result = await CodeDebuggerService(db).review_code("bad code", language="typescript")
    assert result["issues"][0]["severity"] == "info"


# ═══════════════════════════════════════════════════════════════════════════
# GIT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_connect_repository_creates_default_branch(stateful_client):
    _client, db = stateful_client
    repo = await GitManagerService(db).connect_repository(
        "https://github.com/acme/widgets", provider="github",
        token="ghp_x", user_id=uuid.uuid4(), project_id=uuid.uuid4())
    assert repo.name == "widgets"
    branches = [b for b in db.objects_of(BranchRecord) if b.repository_id == repo.id]
    assert len(branches) == 1
    assert branches[0].name == "main"
    assert branches[0].is_default is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_commit_message(stateful_client):
    _client, db = stateful_client
    with _mock_complete("fix: handle empty input"):
        msg = await GitManagerService(db).generate_commit_message("@@ -1,2 +1,2 @@")
    assert msg == "fix: handle empty input"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_repository(stateful_client):
    _client, db = stateful_client
    svc = GitManagerService(db)
    with pytest.raises(ValueError, match="Repository not found"):
        await svc.analyze_repository(uuid.uuid4())

    repo = await svc.connect_repository("https://github.com/a/b")
    commit = CommitRecord(id=uuid.uuid4(), message="initial", branch="main",
                          files_changed=[], additions=0, is_ai_generated=False,
                          repository_id=repo.id, user_id=None)
    db.add(commit)
    with _mock_complete(json.dumps({"analysis": "solid", "recommendations": ["add tests"]})):
        result = await svc.analyze_repository(repo.id)
    assert result["analysis"] == "solid"

    with _mock_complete("no json"):
        result = await svc.analyze_repository(repo.id)
    assert result["recommendations"] == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_branch_and_record_commit(stateful_client):
    _client, db = stateful_client
    svc = GitManagerService(db)
    repo = await svc.connect_repository("https://github.com/a/c")

    branch = await svc.create_branch(repo.id, "feature/login")
    assert branch.name == "feature/login"
    assert branch.repository_id == repo.id

    commit = await svc.record_commit(repo.id, uuid.uuid4(), "add login",
                                     branch="feature/login",
                                     files_changed=["auth.py"], is_ai=True)
    assert commit.additions == 1
    assert commit.is_ai_generated is True
    assert commit.branch == "feature/login"

    commit2 = await svc.record_commit(repo.id, uuid.uuid4(), "no files")
    assert commit2.files_changed == []
    assert commit2.additions == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_review_pull_request(stateful_client):
    _client, db = stateful_client
    svc = GitManagerService(db)
    with _mock_complete(json.dumps({"decision": "approve", "issues": []})):
        result = await svc.review_pull_request("PR", "desc", "diff")
    assert result["decision"] == "approve"

    with _mock_complete("garbage"):
        result = await svc.review_pull_request("PR", "desc", "diff")
    assert result["decision"] == "request_changes"


# ═══════════════════════════════════════════════════════════════════════════
# DEPLOYMENT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_dockerfile_and_compose(stateful_client):
    _client, db = stateful_client
    svc = DeploymentManagerService(db)
    with pytest.raises(ValueError, match="Project not found"):
        await svc.generate_dockerfile(uuid.uuid4())

    proj = _project(db, "Widgets")
    with _mock_complete("FROM python:3.12"):
        assert await svc.generate_dockerfile(proj.id) == "FROM python:3.12"
    with _mock_complete("services:\n  web:"):
        assert await svc.generate_docker_compose(proj.id) == "services:\n  web:"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_project_increments_build_number(stateful_client):
    _client, db = stateful_client
    proj = _project(db)
    db.add(StudioFile(path="main.py", name="main.py", content="x",
                      language="python", size=1, project_id=proj.id))
    svc = DeploymentManagerService(db)

    with _mock_complete("looks ready"):
        build1 = await svc.build_project(proj.id, uuid.uuid4())
    assert build1.build_number == 1
    assert build1.status == "success"
    assert build1.output["files_checked"] == 1

    with _mock_complete("ok"):
        build2 = await svc.build_project(proj.id, uuid.uuid4())
    assert build2.build_number == 2

    with pytest.raises(ValueError, match="Project not found"):
        await svc.build_project(uuid.uuid4(), uuid.uuid4())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deploy_targets(stateful_client):
    _client, db = stateful_client
    proj = _project(db)
    svc = DeploymentManagerService(db)

    with _mock_complete("FROM python"):
        docker_deploy = await svc.deploy(proj.id, target="docker", environment="staging", user_id=uuid.uuid4())
    assert docker_deploy.deployment_number == 1
    assert docker_deploy.target == "docker"
    assert docker_deploy.url is None
    assert docker_deploy.config["dockerfile"] == "FROM python"

    with _mock_complete("FROM python"):
        k8s_deploy = await svc.deploy(proj.id, target="kubernetes", config={"replicas": 2})
    assert k8s_deploy.deployment_number == 2
    assert k8s_deploy.url == "https://kubernetes.omniai.app"
    assert k8s_deploy.config["replicas"] == 2

    with _mock_complete("yaml"):
        netlify = await svc.deploy(proj.id, target="netlify")
    assert netlify.url == "https://netlify.omniai.app"
    assert netlify.config["dockerfile"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_ci_cd(stateful_client):
    _client, db = stateful_client
    with _mock_complete("name: CI"):
        assert await DeploymentManagerService(db).generate_ci_cd(uuid.uuid4(), platform="gitlab") == "name: CI"


# ═══════════════════════════════════════════════════════════════════════════
# SECURITY SCANNER
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scan_project_json_flow(stateful_client):
    _client, db = stateful_client
    proj = _project(db)
    db.add(StudioFile(path="app/db.py", name="db.py", content="SELECT * FROM t",
                      language="python", size=15, project_id=proj.id))
    svc = SecurityScannerService(db)

    payload = {"risk_score": 85, "summary": "critical issues",
               "vulnerabilities": [{"type": "SQL Injection", "severity": "critical"}],
               "recommendations": ["use ORM"], "severity_counts": {"critical": 1}}
    with _mock_complete(json.dumps(payload)):
        scan = await svc.scan_project(proj.id, scan_type="full")
    assert scan.status == "completed"
    assert scan.risk_score == 85
    assert scan.severity_counts["critical"] == 1
    assert json.loads(scan.report)["risk_score"] == 85

    counts = await svc.get_vulnerability_count(proj.id)
    assert counts == {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scan_project_fallback_and_missing(stateful_client):
    _client, db = stateful_client
    svc = SecurityScannerService(db)
    with pytest.raises(ValueError, match="Project not found"):
        await svc.scan_project(uuid.uuid4())

    proj = _project(db)
    with _mock_complete("not json"):
        scan = await svc.scan_project(proj.id)
    assert scan.risk_score == 50
    assert scan.severity_counts == {"critical": 0, "high": 0, "medium": 0, "low": 0}
    assert svc.get_vulnerability_count.__name__  # method exists

    empty = await svc.get_vulnerability_count(uuid.uuid4())
    assert empty == {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}


# ═══════════════════════════════════════════════════════════════════════════
# DOC GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_docs(stateful_client):
    _client, db = stateful_client
    proj = _project(db, "Payments")
    db.add(StudioFile(path="app/main.py", name="main.py", content="x",
                      language="python", size=1, project_id=proj.id))
    svc = DocGeneratorService(db)

    with _mock_complete("# Payments\n\nDocs"):
        readme = await svc.generate(proj.id, doc_type="readme")
    assert readme.title == "README"
    assert readme.format == "markdown"
    assert readme.content.startswith("# Payments")

    with _mock_complete("api docs"):
        api = await svc.generate(proj.id, doc_type="api_docs")
    assert api.title == "API Documentation"

    with _mock_complete("docs"):
        all_docs = await svc.generate_all(proj.id)
    assert len(all_docs) == 5
    assert {d.title for d in all_docs} >= {"README", "API Documentation", "User Manual",
                                          "Developer Guide", "Architecture Documentation"}

    with pytest.raises(ValueError, match="Project not found"):
        await svc.generate(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
# APP GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_app_with_file_tree(stateful_client):
    _client, db = stateful_client
    svc = AppGeneratorService(db)
    payload = {
        "summary": "A todo app",
        "file_tree": {"README.md": "# Todo", "app/main.py": "print('hi')"},
        "architecture": "monolith",
        "setup_instructions": "pip install -r",
    }
    with _mock_complete(json.dumps(payload)):
        project = await svc.generate(
            name="Todo App", description="tasks", project_type="web",
            language="python", frontend_framework="react",
            backend_framework="fastapi", database_type="postgresql",
        )
    assert project.status == "generated"
    assert project.file_tree == {"README.md": "file", "app/main.py": "file"}
    assert project.config["summary"] == "A todo app"

    files = [f for f in db.objects_of(StudioFile) if f.project_id == project.id]
    assert {f.path for f in files} == {"README.md", "app/main.py"}
    assert {f.name for f in files} == {"README.md", "main.py"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_app_invalid_json_fallback(stateful_client):
    _client, db = stateful_client
    svc = AppGeneratorService(db)
    with _mock_complete("here is your app code, no json"):
        project = await svc.generate(name="X", description="d", project_type="web", language="python")
    assert project.status == "generated"
    assert "README.md" in project.file_tree
    assert project.config["architecture"] == "Single file"


# ═══════════════════════════════════════════════════════════════════════════
# CHAT SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_message_updates_new_chat_title(stateful_client):
    _client, db = stateful_client
    user_id = uuid.uuid4()
    session = ChatSession(id=uuid.uuid4(), user_id=user_id, title="New Chat", model="gpt-4o")
    db.add(session)
    svc = ChatService(db)
    responses = [
        {"content": "Hello! How can I help?", "tokens_used": 12},
        {"content": "\"Billing Help\"", "tokens_used": 5},
    ]
    with patch("app.services.ai_service.ai_service.complete",
               AsyncMock(side_effect=responses)):
        reply = await svc.send_message(session.id, user_id, ChatMessageSendRequest(content="hi there"))

    assert reply.content == "Hello! How can I help?"
    assert session.title == "Billing Help"
    assert session.title.endswith('"') is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_message_keeps_custom_title(stateful_client):
    _client, db = stateful_client
    user_id = uuid.uuid4()
    session = ChatSession(id=uuid.uuid4(), user_id=user_id, title="My Topic", model="gpt-4o")
    db.add(session)
    with _mock_complete("Hola"):
        reply = await ChatService(db).send_message(session.id, user_id, ChatMessageSendRequest(content="yo"))
    assert reply.content == "Hola"
    assert session.title == "My Topic"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_message_missing_or_foreign_session(stateful_client):
    _client, db = stateful_client
    user_id = uuid.uuid4()
    svc = ChatService(db)
    with pytest.raises(NotFoundError, match="Chat session"):
        await svc.send_message(uuid.uuid4(), user_id, ChatMessageSendRequest(content="hi"))

    other = ChatSession(id=uuid.uuid4(), user_id=uuid.uuid4(), title="T", model="gpt-4o")
    db.add(other)
    with pytest.raises(NotFoundError):
        await svc.send_message(other.id, user_id, ChatMessageSendRequest(content="hi"))


# ═══════════════════════════════════════════════════════════════════════════
# AGENT COMMUNICATION
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_direct_message_no_ai(stateful_client):
    _client, db = stateful_client
    sender, receiver = uuid.uuid4(), uuid.uuid4()
    svc = AgentCommunicationService(db)
    with _mock_complete("never called"):
        msg = await svc.send_message(sender, receiver, "ping", "direct",
                                     metadata={"priority": 1}, task_id=uuid.uuid4())
    assert msg.content == "ping"
    assert msg.sender_id == sender
    assert msg.receiver_id == receiver
    assert msg.meta_data == {"priority": 1}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_ai_formatted_message(stateful_client):
    _client, db = stateful_client
    svc = AgentCommunicationService(db)
    with _mock_complete("STANDUP REPORT"):
        msg = await svc.send_message(uuid.uuid4(), uuid.uuid4(), "raw", "briefing")
    assert msg.content == "STANDUP REPORT"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_broadcast(stateful_client):
    _client, db = stateful_client
    sender = uuid.uuid4()
    receivers = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    svc = AgentCommunicationService(db)
    with _mock_complete("all hands"):
        messages = await svc.send_broadcast(sender, receivers, "all hands", team_id=uuid.uuid4())
    assert len(messages) == 3
    assert all(m.content == "all hands" for m in messages)


# ═══════════════════════════════════════════════════════════════════════════
# AGENT EVALUATION
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_review_output_approves_good_work(stateful_client):
    _client, db = stateful_client
    reviewer, reviewee = uuid.uuid4(), uuid.uuid4()
    content = (
        "Score: 8.5\n"
        "Confidence: 0.9\n"
        "Overall the output is accurate and complete.\n"
        "Suggestions: Add more edge cases."
    )
    with _mock_complete(content):
        review = await AgentEvaluationService(db).review_output(
            reviewer, reviewee, "agent output", criteria={"clarity": 9})
    assert review.score == 8.5
    assert review.review_type == "peer"
    assert review.is_approved is True
    assert review.confidence == 0.9
    assert review.criteria_scores == {"clarity": 9}

    perf = await AgentEvaluationService(db).get_performance(reviewee)
    assert perf is not None
    assert perf.total_tasks == 1
    assert perf.avg_score == 8.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_review_output_rejects_poor_work_and_self_review(stateful_client):
    _client, db = stateful_client
    agent = uuid.uuid4()
    with _mock_complete("Score: 3\nConfidence: 0.4\nPoor accuracy."):
        review = await AgentEvaluationService(db).self_review(agent, "bad output")
    assert review.review_type == "self"
    assert review.is_approved is False
    assert review.score == 3.0

    reviews = await AgentEvaluationService(db).get_agent_reviews(agent)
    assert len(reviews) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_review_output_defaults_when_no_score(stateful_client):
    _client, db = stateful_client
    with _mock_complete("No explicit score, but fine."):
        review = await AgentEvaluationService(db).review_output(uuid.uuid4(), uuid.uuid4(), "x")
    assert review.score == 7.0
    assert review.is_approved is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_performance_none_when_missing(stateful_client):
    _client, db = stateful_client
    assert await AgentEvaluationService(db).get_performance(uuid.uuid4()) is None

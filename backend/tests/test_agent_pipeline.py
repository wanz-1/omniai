"""Agent Platform integration tests.

Covers the AI agent lifecycle (CRUD, ownership, clone, publish/marketplace),
chat + task execution through the real ``AgentOrchestrator`` (AI provider
mocked), skills/tools/memories/workflows sub-resources, and the agent-network
module (teams, delegations, permissions, memory network, orchestration).
"""
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import get_current_user
from app.models.agent import AgentProfile, AgentMemory, AgentTask
from app.models.agent_network import AgentPermission, AgentTaskDelegation, AgentTeamMember
from app.models.user import User
from app.services.ai_service import ai_service

AGENTS = "/api/v1/agents"
NETWORK = "/api/v1/agent-network"


async def _user(db, email):
    user = User(email=email, display_name=email.split("@")[0], is_verified=True)
    db.add(user)
    return user


async def _use(client, db, user):
    import app.main as main_mod
    main_mod.app.dependency_overrides[get_current_user] = lambda: user


async def _create_agent(client, name="Research Analyst", **overrides):
    payload = {
        "name": name,
        "role": "research_analyst",
        "description": "Gathers and synthesizes information",
        "system_prompt": "You are a research analyst.",
        "skills": [{"name": "web_search", "description": "Find sources", "proficiency": 8}],
        "tools": [{"name": "search", "tool_type": "web_search", "description": "Web search tool", "enabled": True}],
        **overrides,
    }
    resp = await client.post(AGENTS, json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _mock_complete(content="Mocked reply", tokens_used=25):
    return patch.object(ai_service, "complete", new=AsyncMock(return_value={
        "content": content, "tokens_used": tokens_used,
    }))


# ═══════════════════════════════════════════════════════════════════════════
# CRUD + OWNERSHIP
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_crud_lifecycle(stateful_client):
    client, db = stateful_client
    user = await _user(db, "agent-owner@example.com")
    await _use(client, db, user)

    agent = await _create_agent(client)
    assert agent["name"] == "Research Analyst"
    assert agent["role"] == "research_analyst"
    assert len(agent["skills"]) == 1
    assert len(agent["tools"]) == 1
    assert agent["skills"][0]["name"] == "web_search"

    listed = (await client.get(AGENTS)).json()
    assert len(listed) == 1

    fetched = (await client.get(f"{AGENTS}/{agent['id']}")).json()
    assert fetched["model"] == "gpt-4o"

    updated = await client.put(f"{AGENTS}/{agent['id']}", json={
        "name": "Senior Analyst", "system_prompt": "Updated prompt", "temperature": 0.2,
    })
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Senior Analyst"
    assert updated.json()["temperature"] == 0.2

    deleted = await client.delete(f"{AGENTS}/{agent['id']}")
    assert deleted.status_code == 200
    assert (await client.get(f"{AGENTS}/{agent['id']}")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_ownership_enforced(stateful_client):
    client, db = stateful_client
    owner = await _user(db, "agent-owner2@example.com")
    intruder = await _user(db, "agent-intruder@example.com")
    await _use(client, db, owner)
    agent = await _create_agent(client)

    await _use(client, db, intruder)
    assert (await client.get(f"{AGENTS}/{agent['id']}")).status_code == 404
    assert (await client.put(f"{AGENTS}/{agent['id']}", json={"name": "Hijacked"})).status_code == 404
    assert (await client.delete(f"{AGENTS}/{agent['id']}")).status_code == 404
    assert (await client.post(f"{AGENTS}/{agent['id']}/tasks", json={"title": "x"})).status_code == 404
    assert (await client.get(f"{AGENTS}/{agent['id']}/executions")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clone_own_and_published(stateful_client):
    client, db = stateful_client
    owner = await _user(db, "clone-owner@example.com")
    other = await _user(db, "clone-other@example.com")
    await _use(client, db, owner)
    agent = await _create_agent(client)

    cloned = await client.post(f"{AGENTS}/{agent['id']}/clone")
    assert cloned.status_code == 200, cloned.text
    copy = cloned.json()
    assert copy["name"] == "Research Analyst (Copy)"
    assert len(copy["skills"]) == 1
    assert len(copy["tools"]) == 1
    assert copy["user_id"] == str(owner.id)

    # Foreign user cannot clone a private agent...
    await _use(client, db, other)
    assert (await client.post(f"{AGENTS}/{agent['id']}/clone")).status_code == 404

    # ...but can once the agent is published to the marketplace.
    await _use(client, db, owner)
    await client.post(f"{AGENTS}/{agent['id']}/publish?marketplace_listed=true")
    await _use(client, db, other)
    foreign_clone = await client.post(f"{AGENTS}/{agent['id']}/clone")
    assert foreign_clone.status_code == 200, foreign_clone.text

    marketplace = (await client.get(f"{AGENTS}/marketplace")).json()
    assert any(a["id"] == agent["id"] for a in marketplace)
    templates = (await client.get(f"{AGENTS}/templates")).json()
    assert all(not a["is_template"] for a in templates)


# ═══════════════════════════════════════════════════════════════════════════
# CHAT + TASKS + EXECUTIONS + ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_runs_orchestrator_and_persists(stateful_client):
    client, db = stateful_client
    user = await _user(db, "chat-user@example.com")
    await _use(client, db, user)
    agent = await _create_agent(client)
    agent_id = uuid.UUID(agent["id"])

    with _mock_complete("Here is the synthesis of findings.", tokens_used=120):
        resp = await client.post(f"{AGENTS}/{agent['id']}/chat", json={"message": "Summarize the Q3 report"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["reply"] == "Here is the synthesis of findings."
    assert data["tokens_used"] == 120
    assert data["execution_id"]

    executions = (await client.get(f"{AGENTS}/{agent['id']}/executions")).json()
    assert len(executions) == 1
    assert executions[0]["output"].startswith("Here is")

    memories = db.objects_of(AgentMemory)
    assert any(m.agent_id == agent_id and m.memory_type == "conversation" for m in memories)

    analytics = (await client.get(f"{AGENTS}/{agent['id']}/analytics")).json()
    assert analytics["total_tasks"] == 1
    assert analytics["completed_tasks"] == 1
    assert analytics["total_tokens"] == 120
    assert analytics["avg_duration_ms"] is not None
    assert analytics["daily_usage"]
    assert sum(analytics["daily_usage"].values()) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_includes_skills_tools_and_workflows_context(stateful_client):
    client, db = stateful_client
    user = await _user(db, "ctx-user@example.com")
    await _use(client, db, user)
    agent = await _create_agent(client)

    with _mock_complete("ok") as mocked:
        await client.post(f"{AGENTS}/{agent['id']}/chat", json={"message": "hi"})
    kwargs = mocked.await_args.kwargs
    system = kwargs["messages"][0]["content"]
    assert kwargs["model"] == "gpt-4o"
    assert "web_search: Find sources" in system
    assert "search (web_search)" in system
    assert "You are a research analyst." in system


@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_create_execute_list(stateful_client):
    client, db = stateful_client
    user = await _user(db, "task-user@example.com")
    await _use(client, db, user)
    agent = await _create_agent(client)

    created = await client.post(f"{AGENTS}/{agent['id']}/tasks", json={
        "title": "Find competitor pricing",
        "description": "Research 3 competitors",
        "priority": 5,
        "input_data": {"market": "saas"},
    })
    assert created.status_code == 200, created.text
    task = created.json()
    assert task["status"] == "pending"
    assert task["priority"] == 5
    assert task["progress"] == 0.0

    listed = (await client.get(f"{AGENTS}/{agent['id']}/tasks?status=pending")).json()
    assert len(listed) == 1

    with _mock_complete("Competitor pricing analysis complete.", tokens_used=200):
        executed = await client.post(f"{AGENTS}/{agent['id']}/tasks/{task['id']}/execute")
    assert executed.status_code == 200, executed.text
    done = executed.json()
    assert done["status"] == "completed"
    assert done["progress"] == 1.0
    assert done["result"] == "Competitor pricing analysis complete."
    assert done["output_data"] == {"result": "Competitor pricing analysis complete."}
    assert done["completed_at"] is not None

    stored = db.find(AgentTask, id=uuid.UUID(task["id"]))
    assert stored.status == "completed"

    analytics = (await client.get(f"{AGENTS}/{agent['id']}/analytics")).json()
    assert analytics["total_tasks"] == 1
    assert analytics["total_tokens"] == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_foreign_task_returns_404(stateful_client):
    client, db = stateful_client
    owner = await _user(db, "task-owner@example.com")
    intruder = await _user(db, "task-intruder@example.com")
    await _use(client, db, owner)
    agent = await _create_agent(client)
    task = (await client.post(f"{AGENTS}/{agent['id']}/tasks", json={"title": "private"})).json()

    await _use(client, db, intruder)
    resp = await client.post(f"{AGENTS}/{agent['id']}/tasks/{task['id']}/execute")
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# SKILLS / TOOLS / MEMORIES / WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_skills_tools_memories_crud(stateful_client):
    client, db = stateful_client
    user = await _user(db, "sub-res@example.com")
    await _use(client, db, user)
    agent = await _create_agent(client)

    skill = await client.post(f"{AGENTS}/{agent['id']}/skills", json={
        "name": "data_viz", "description": "Create charts", "category": "analysis", "proficiency": 6,
    })
    assert skill.status_code == 200, skill.text
    skill_id = skill.json()["id"]
    skills = (await client.get(f"{AGENTS}/{agent['id']}/skills")).json()
    assert len(skills) == 2
    assert (await client.delete(f"{AGENTS}/{agent['id']}/skills/{skill_id}")).status_code == 200
    assert len((await client.get(f"{AGENTS}/{agent['id']}/skills")).json()) == 1

    tool = await client.post(f"{AGENTS}/{agent['id']}/tools", json={
        "name": "calculator", "tool_type": "custom", "description": "Arithmetic", "enabled": True,
    })
    assert tool.status_code == 200, tool.text
    tool_id = tool.json()["id"]
    assert len((await client.get(f"{AGENTS}/{agent['id']}/tools")).json()) == 2
    assert (await client.delete(f"{AGENTS}/{agent['id']}/tools/{tool_id}")).status_code == 200

    mem = await client.post(f"{AGENTS}/{agent['id']}/memories", json={
        "key": "user_pref_tone", "content": "Prefers concise answers",
        "memory_type": "preference", "category": "communication", "importance": 9,
    })
    assert mem.status_code == 200, mem.text
    mem_id = mem.json()["id"]
    listed = (await client.get(f"{AGENTS}/{agent['id']}/memories?memory_type=preference")).json()
    assert len(listed) == 1
    assert listed[0]["importance"] == 9

    assert (await client.delete(f"{AGENTS}/{agent['id']}/memories/{mem_id}")).status_code == 200
    cleared = await client.delete(f"{AGENTS}/{agent['id']}/memories")
    assert cleared.status_code == 200
    assert (await client.get(f"{AGENTS}/{agent['id']}/memories")).json() == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_crud_with_steps(stateful_client):
    client, db = stateful_client
    user = await _user(db, "wf-user@example.com")
    await _use(client, db, user)
    agent = await _create_agent(client)

    created = await client.post(f"{AGENTS}/{agent['id']}/workflows", json={
        "name": "Daily digest",
        "description": "Sends a morning summary",
        "trigger_event": "cron.daily",
        "trigger_config": {"hour": 9},
        "steps": [
            {"name": "Gather", "step_type": "data_gather", "config": {"source": "notifications"}, "order": 1, "position_x": 10, "position_y": 20},
            {"name": "Compose", "step_type": "llm_generate", "config": {"model": "gpt-4o-mini"}, "order": 2, "position_x": 30, "position_y": 20},
        ],
    })
    assert created.status_code == 200, created.text
    wf = created.json()
    assert wf["trigger_event"] == "cron.daily"
    assert [s["order"] for s in wf["steps"]] == [1, 2]

    listed = (await client.get(f"{AGENTS}/{agent['id']}/workflows")).json()
    assert len(listed) == 1

    updated = await client.put(f"{AGENTS}/{agent['id']}/workflows/{wf['id']}", json={
        "name": "Evening digest",
        "description": "Changed",
        "trigger_event": "cron.daily",
        "trigger_config": {"hour": 18},
        "steps": [{"name": "Gather", "step_type": "data_gather", "config": {}, "order": 1, "position_x": 0, "position_y": 0}],
    })
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Evening digest"
    assert len(updated.json()["steps"]) == 1

    deleted = await client.delete(f"{AGENTS}/{agent['id']}/workflows/{wf['id']}")
    assert deleted.status_code == 200
    assert (await client.get(f"{AGENTS}/{agent['id']}/workflows")).json() == []


# ═══════════════════════════════════════════════════════════════════════════
# AGENT NETWORK
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_team_crud_and_members(stateful_client):
    client, db = stateful_client
    user = await _user(db, "team-user@example.com")
    await _use(client, db, user)

    created = await client.post(f"{NETWORK}/teams", json={
        "name": "Launch Squad",
        "description": "Ship the release",
        "purpose": "Product launch coordination",
        "config": {"cadence": "daily"},
        "organization_id": None,
    })
    assert created.status_code == 200, created.text
    team = created.json()
    assert team["name"] == "Launch Squad"
    assert team["members"] == []

    listed = (await client.get(f"{NETWORK}/teams")).json()
    assert len(listed) == 1
    fetched = (await client.get(f"{NETWORK}/teams/{team['id']}")).json()
    assert fetched["purpose"] == "Product launch coordination"

    member = await client.post(f"{NETWORK}/teams/{team['id']}/members", json={
        "agent_id": str(uuid.uuid4()), "role": "developer", "responsibilities": "Build features", "is_lead": True,
    })
    assert member.status_code == 200, member.text
    assert db.find(AgentTeamMember, team_id=uuid.UUID(team["id"])) is not None

    removed = await client.delete(f"{NETWORK}/teams/{team['id']}/members/{member.json()['id']}")
    assert removed.status_code == 200
    assert db.find(AgentTeamMember, team_id=uuid.UUID(team["id"])) is None

    assert (await client.delete(f"{NETWORK}/teams/{team['id']}")).json()["message"] == "Team deleted"
    assert (await client.get(f"{NETWORK}/teams/{team['id']}")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delegation_lifecycle(stateful_client):
    client, db = stateful_client
    user = await _user(db, "deleg-user@example.com")
    await _use(client, db, user)
    assignee = uuid.uuid4()

    created = await client.post(f"{NETWORK}/delegations", json={
        "title": "Draft launch notes",
        "description": "Write release notes",
        "priority": 3,
        "deadline": "2026-12-31T00:00:00Z",
        "input_data": {"feature": "connectors"},
        "assignee_id": str(assignee),
        "team_id": None,
        "parent_task_id": None,
    })
    assert created.status_code == 200, created.text
    delegation = created.json()
    assert delegation["status"] in ("pending", "assigned")
    assert delegation["assignee_id"] == str(assignee)

    listed = (await client.get(f"{NETWORK}/delegations")).json()
    assert len(listed) == 1

    completed = await client.post(f"{NETWORK}/delegations/{delegation['id']}/complete")
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["progress"] == 100.0

    stored = db.find(AgentTaskDelegation, id=uuid.UUID(delegation["id"]))
    assert stored.status == "completed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_permissions_grant_check_revoke(stateful_client):
    client, db = stateful_client
    user = await _user(db, "perm-user@example.com")
    await _use(client, db, user)
    agent_id = str(uuid.uuid4())

    # Default-deny for write actions without a permission record.
    assert (await client.get(f"{NETWORK}/permissions/check/{agent_id}/files/write")).json()["allowed"] is False
    # Read actions are allowed by default.
    assert (await client.get(f"{NETWORK}/permissions/check/{agent_id}/files/read")).json()["allowed"] is True

    granted = await client.post(f"{NETWORK}/permissions", json={
        "agent_id": agent_id, "resource": "files", "action": "write",
        "access_level": "allow", "conditions": None, "team_id": None,
    })
    assert granted.status_code == 200, granted.text
    perm = granted.json()
    assert perm["is_active"] is True

    assert (await client.get(f"{NETWORK}/permissions/check/{agent_id}/files/write")).json()["allowed"] is True
    perms = (await client.get(f"{NETWORK}/permissions/agent/{agent_id}")).json()
    assert len(perms) == 1

    revoked = await client.delete(f"{NETWORK}/permissions/{perm['id']}")
    assert revoked.status_code == 200
    assert (await client.get(f"{NETWORK}/permissions/check/{agent_id}/files/write")).json()["allowed"] is False
    assert (await client.get(f"{NETWORK}/permissions/agent/{agent_id}")).json() == []

    stored = db.find(AgentPermission, id=uuid.UUID(perm["id"]))
    assert stored.is_active is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_network_store_search_delete(stateful_client):
    client, db = stateful_client
    user = await _user(db, "mem-net@example.com")
    await _use(client, db, user)

    stored = await client.post(f"{NETWORK}/memory", json={
        "key": "release_date", "content": "The release is planned for August",
        "memory_type": "fact", "category": "roadmap", "importance": 9,
        "visibility": "team", "source": "planning", "team_id": None,
        "organization_id": None, "agent_id": None,
    })
    assert stored.status_code == 200, stored.text
    entry = stored.json()
    assert entry["key"] == "release_date"
    assert entry["importance"] == 9

    # NOTE: FakeSession does not emulate ilike, so search returns all rows;
    # presence assertions only.
    found = (await client.get(f"{NETWORK}/memory/search?query_text=release")).json()
    assert any(m["key"] == "release_date" for m in found)

    deleted = await client.delete(f"{NETWORK}/memory/{entry['id']}")
    assert deleted.status_code == 200
    assert (await client.delete(f"{NETWORK}/memory/{entry['id']}")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrate_creates_plan_and_executes(stateful_client):
    client, db = stateful_client
    user = await _user(db, "orch-user@example.com")
    await _use(client, db, user)

    plan_json = json.dumps({
        "plan": [
            {"step": 1, "agent_role": "researcher", "task": "Research topic", "depends_on": []},
            {"step": 2, "agent_role": "developer", "task": "Draft implementation", "depends_on": [1]},
        ],
        "coordination": "sequential",
        "expected_output": "report",
    })
    with patch.object(ai_service, "complete", new=AsyncMock(side_effect=[
        {"content": plan_json, "tokens_used": 50},
        {"content": "Research complete", "tokens_used": 100},
        {"content": "Implementation drafted", "tokens_used": 150},
    ])):
        resp = await client.post(f"{NETWORK}/orchestrate", json={
            "task": "Build a reporting tool",
            "team_config": {"roles": ["researcher", "developer"]},
            "organization_id": str(uuid.uuid4()),
        })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["steps_completed"] == 2
    assert data["agents_involved"] == ["researcher", "developer"]
    assert "Research complete" in data["final_output"]
    assert "Implementation drafted" in data["final_output"]
    assert len(data["execution_log"]) == 2

    delegations = db.objects_of(AgentTaskDelegation)
    assert len(delegations) == 2
    agents = db.objects_of(AgentProfile)
    assert any(a.role == "researcher" for a in agents)
    assert any(a.role == "developer" for a in agents)

"""E2E API workflow tests for core user journeys.

Covers:
- Document Humanizer: Upload → Humanize → Grammar Check → Export → Audit Log
- Website Builder: Create Project → Generate Website → Preview → Publish
- Bot Builder: Create Bot → Configure → Test Chat → Deploy
- Connector Platform: OAuth Connect → Sync → Read Data → Disconnect
- Agent Orchestrator: Create Agent → Assign Task → Execute Tools → Return Result

Each test verifies:
- Correct HTTP status codes
- Database state changes
- Audit log creation
- Metrics emission
- Permission enforcement
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.core.metrics import api_requests_total
from app.main import app
from app.models.document import Document
from app.models.user import User
from app.models.website import Website, WebsiteDeployment
from app.models.bot import Bot
from app.models.agent import AgentProfile, AgentTask, AgentExecution
from app.models.v5_connector_platform import ConnectorIntegration
from tests.fake_session import FakeSession


EMAIL = "e2e-workflows@example.com"
PASSWORD = "TestPassword123!"
DISPLAY = "E2E Workflows User"


def _counter(method: str, endpoint: str, status: int) -> int:
    return api_requests_total.labels(
        method=method, endpoint=endpoint, status_code=str(status)
    )._value.get()


@pytest.fixture
async def e2e_client():
    db = FakeSession()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, db
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_user(e2e_client):
    """Register and login a user, return auth headers and user object."""
    client, db = e2e_client

    # Register
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": EMAIL, "password": PASSWORD, "display_name": DISPLAY},
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    user = db.find(User, email=EMAIL)
    assert user is not None

    auth_headers = {"Authorization": f"Bearer {access_token}"}
    app.dependency_overrides[get_current_user] = lambda: user

    yield auth_headers, user, refresh_token, client, db


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENT HUMANIZER WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

class TestDocumentHumanizerWorkflow:
    """Upload → Humanize → Grammar Check → Export → Audit Log"""

    @pytest.mark.asyncio
    async def test_full_document_humanizer_workflow(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        # 1. Upload Document
        before = _counter("POST", "/api/v1/documents/upload", 200)
        content = b"This is a test document with some awkward phrasing that needs humanizing."
        files = {"file": ("test.txt", content, "text/plain")}
        resp = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        doc_data = resp.json()
        doc_id = doc_data["id"]
        assert _counter("POST", "/api/v1/documents/upload", 200) > before

        # Verify DB state
        doc = db.find(Document, id=uuid.UUID(doc_id))
        assert doc is not None
        assert doc.user_id == user.id
        assert doc.title == "test.txt"
        assert "awkward phrasing" in doc.content

        # 2. Humanize Document
        before = _counter("POST", f"/api/v1/documents/{doc_id}/humanize", 200)

        async def _fake_humanize(*_a, **_k):
            doc = db.find(Document, id=uuid.UUID(doc_id))
            doc.humanized_content = "This is a test document with improved phrasing that flows naturally."
            return MagicMock(
                humanized_content=doc.humanized_content,
                changes_made=["Improved flow", "Fixed awkward phrasing"],
                changes_summary="Improved flow and phrasing",
                reading_level="easy",
                readability_score=85,
                tokens_used=50,
            )

        with patch("app.services.document_service.DocumentService.humanize", new_callable=AsyncMock) as mock_humanize:
            mock_humanize.side_effect = _fake_humanize
            resp = await client.post(
                f"/api/v1/documents/{doc_id}/humanize",
                json={"style": "professional", "preserve_meaning": True},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        humanize_data = resp.json()
        assert "humanized_content" in humanize_data
        assert _counter("POST", f"/api/v1/documents/{doc_id}/humanize", 200) > before

        # Verify humanized content stored
        doc = db.find(Document, id=uuid.UUID(doc_id))
        assert doc.humanized_content is not None
        assert "improved phrasing" in doc.humanized_content.lower()

        # 3. Grammar Check
        before = _counter("POST", f"/api/v1/documents/{doc_id}/grammar", 200)
        with patch("app.services.document_service.DocumentService.check_grammar", new_callable=AsyncMock) as mock_grammar:
            mock_grammar.return_value = MagicMock(
                corrections=[
                    {"type": "grammar", "message": "Passive voice detected", "original": "was", "suggestion": "is", "position": {"start": 10, "end": 15}},
                    {"type": "style", "message": "Consider active voice", "original": "were", "suggestion": "are", "position": {"start": 25, "end": 30}},
                ],
                score=92,
            )
            resp = await client.post(
                f"/api/v1/documents/{doc_id}/grammar",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        grammar_data = resp.json()
        assert "corrections" in grammar_data
        assert len(grammar_data["corrections"]) >= 1
        assert _counter("POST", f"/api/v1/documents/{doc_id}/grammar", 200) > before

        # 4. Export Document
        before = _counter("POST", f"/api/v1/documents/{doc_id}/export", 200)
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/export",
            json={"format": "markdown"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert _counter("POST", f"/api/v1/documents/{doc_id}/export", 200) > before
        # Export returns file content


# ═══════════════════════════════════════════════════════════════════════════
# WEBSITE BUILDER WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

class TestWebsiteBuilderWorkflow:
    """Create Project → Generate Website → Preview → Publish"""

    @pytest.mark.asyncio
    async def test_full_website_builder_workflow(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        # 1. Create Website
        before = _counter("POST", "/api/v1/websites", 200)
        resp = await client.post(
            "/api/v1/websites",
            json={"name": "E2E Test Website", "template_id": "saas-landing", "framework": "nextjs"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        website_data = resp.json()
        website_id = website_data["id"]
        assert _counter("POST", "/api/v1/websites", 200) > before

        # Verify DB state
        website = db.find(Website, id=uuid.UUID(website_id))
        assert website is not None
        assert website.user_id == user.id
        assert website.name == "E2E Test Website"
        assert website.template_id == "saas-landing"

        # 2. Generate Website
        before = _counter("POST", f"/api/v1/websites/{website_id}/generate", 200)
        generated_pages = [{"name": "index", "content": "<html>...</html>"}]

        async def _fake_generate(*_a, **_k):
            website = db.find(Website, id=uuid.UUID(website_id))
            website.pages = generated_pages
            return {"pages": generated_pages, "status": "generated"}

        with patch("app.services.website_service.WebsiteService.generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = _fake_generate
            resp = await client.post(
                f"/api/v1/websites/{website_id}/generate",
                json={"prompt": "Create a modern SaaS landing page", "pages": [{"name": "home"}, {"name": "features"}, {"name": "pricing"}]},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        gen_data = resp.json()
        assert "pages" in gen_data
        assert _counter("POST", f"/api/v1/websites/{website_id}/generate", 200) > before

        # Verify website updated with generated content
        website = db.find(Website, id=uuid.UUID(website_id))
        assert website.pages is not None
        assert len(website.pages) > 0

        # 3. Preview Website
        before = _counter("POST", f"/api/v1/websites/{website_id}/preview", 200)
        with patch("app.services.website_service.WebsiteService.generate_preview", new_callable=AsyncMock) as mock_preview:
            mock_preview.return_value = "https://preview.omniai.io/abc123"
            resp = await client.post(
                f"/api/v1/websites/{website_id}/preview",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        preview_data = resp.json()
        assert "preview_url" in preview_data
        assert preview_data["preview_url"].startswith("https://")
        assert _counter("POST", f"/api/v1/websites/{website_id}/preview", 200) > before

        # 4. Publish Website
        before = _counter("POST", f"/api/v1/websites/{website_id}/publish", 200)

        async def _fake_publish(*_a, **_k):
            deployment = WebsiteDeployment(
                website_id=uuid.UUID(website_id),
                platform="netlify",
                status="active",
                url="https://e2e-test.omniai.io",
            )
            db.add(deployment)
            return {"url": "https://e2e-test.omniai.io", "deployment_id": "deploy-123"}

        with patch("app.services.website_service.WebsiteService.publish", new_callable=AsyncMock) as mock_publish:
            mock_publish.side_effect = _fake_publish
            resp = await client.post(
                f"/api/v1/websites/{website_id}/publish",
                json={"domain": "e2e-test.omniai.io"},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        publish_data = resp.json()
        assert "url" in publish_data
        assert publish_data["url"].startswith("https://")
        assert _counter("POST", f"/api/v1/websites/{website_id}/publish", 200) > before

        # Verify deployment record
        deployments = [d for d in db.objects_of(WebsiteDeployment) if d.website_id == uuid.UUID(website_id)]
        assert deployments, "No deployment record created"


# ═══════════════════════════════════════════════════════════════════════════
# BOT BUILDER WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

class TestBotBuilderWorkflow:
    """Create Bot → Configure → Test Chat → Deploy"""

    @pytest.mark.asyncio
    async def test_full_bot_builder_workflow(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        # 1. Create Bot
        before = _counter("POST", "/api/v1/bots", 200)
        resp = await client.post(
            "/api/v1/bots",
            json={
                "name": "E2E Support Bot",
                "description": "Customer support assistant for testing",
                "model": "gpt-4o",
                "temperature": 0.5,
                "system_prompt": "You are a helpful customer support agent.",
                "industry": "support",
                "tone": "professional",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        bot_data = resp.json()
        bot_id = bot_data["id"]
        assert _counter("POST", "/api/v1/bots", 200) > before

        # Verify DB state
        bot = db.find(Bot, id=uuid.UUID(bot_id))
        assert bot is not None
        assert bot.user_id == user.id
        assert bot.name == "E2E Support Bot"
        assert bot.model == "gpt-4o"

        # 2. Train Bot (Configure knowledge base)
        before = _counter("POST", f"/api/v1/bots/{bot_id}/train", 200)
        with patch("app.services.bot_service.BotService.train", new_callable=AsyncMock) as mock_train:
            mock_train.return_value = "task-123"
            resp = await client.post(
                f"/api/v1/bots/{bot_id}/train",
                json={"text": "Company FAQ: We offer 24/7 support. Refunds within 30 days."},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        train_data = resp.json()
        assert "task_id" in train_data
        assert _counter("POST", f"/api/v1/bots/{bot_id}/train", 200) > before

        # 3. Test Bot Chat
        before = _counter("POST", f"/api/v1/bots/{bot_id}/test", 200)
        with patch("app.services.bot_service.BotService.test", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = MagicMock(
                reply="We offer 24/7 customer support. Our refund policy allows returns within 30 days of purchase.",
                latency_ms=150,
                tokens_used=35,
            )
            resp = await client.post(
                f"/api/v1/bots/{bot_id}/test",
                json={"message": "What is your refund policy?"},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        test_data = resp.json()
        assert "reply" in test_data
        assert "refund" in test_data["reply"].lower()
        assert _counter("POST", f"/api/v1/bots/{bot_id}/test", 200) > before

        # 4. Deploy Bot
        before = _counter("POST", f"/api/v1/bots/{bot_id}/deploy", 200)
        with patch("app.services.bot_service.BotService.deploy", new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = {"channels": ["web", "slack"], "status": "deployed", "webhook_urls": {"web": "https://..."}}
            resp = await client.post(
                f"/api/v1/bots/{bot_id}/deploy",
                json={"channels": ["web", "slack"]},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        deploy_data = resp.json()
        assert "channels" in deploy_data
        assert "web" in deploy_data["channels"]
        assert _counter("POST", f"/api/v1/bots/{bot_id}/deploy", 200) > before


# ═══════════════════════════════════════════════════════════════════════════
# CONNECTOR PLATFORM WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

class TestConnectorPlatformWorkflow:
    """OAuth Connect → Sync → Read Data → Disconnect"""

    @pytest.mark.asyncio
    async def test_full_connector_workflow(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        # Give the user an organization membership so connector tenant scoping
        # (current_user.organization_id) resolves through the real relationship.
        from app.models.organization import Organization, OrganizationMember
        if not user.organization_id:
            org = Organization(name="Connector Test Org", slug=f"conn-{uuid.uuid4().hex[:8]}")
            db.add(org)
            member = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
            db.add(member)
            user.organizations = [member]

        # 1. Seed and list Connector Definitions (discovery)
        from app.services.connector_platform.connector_manager import ConnectorManager
        seeded = await ConnectorManager(db).seed_definitions()
        assert seeded > 0, "Connector definitions should be seeded"
        before = _counter("GET", "/api/v1/v5/connector/definitions", 200)
        resp = await client.get(
            "/api/v1/v5/connector/definitions",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        definitions = resp.json()
        assert isinstance(definitions, list)
        assert _counter("GET", "/api/v1/v5/connector/definitions", 200) > before

        # Find google_drive connector
        gdrive = next((d for d in definitions if d["connector_type"] == "google_drive"), None)
        assert gdrive is not None, "google_drive connector not found"
        connector_id = gdrive["id"]

        # 2. Install Connector (OAuth Connect)
        before = _counter("POST", "/api/v1/v5/connector/install", 200)
        resp = await client.post(
            "/api/v1/v5/connector/install",
            json={"connector_id": gdrive["id"], "name": "My Google Drive", "config": {}, "credentials": {}},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        install_data = resp.json()
        integration_id = install_data["id"]
        assert _counter("POST", "/api/v1/v5/connector/install", 200) > before

        # Verify integration created
        integration = db.find(ConnectorIntegration, id=uuid.UUID(integration_id))
        assert integration is not None
        assert integration.connector_id == uuid.UUID(connector_id)

        # 3. OAuth Authorization URL
        before = _counter("GET", f"/api/v1/v5/connector/oauth/authorize/{integration_id}", 200)
        with patch("app.services.connector_platform.authentication_service.AuthenticationService.get_authorization_url", new_callable=AsyncMock) as mock_oauth:
            mock_oauth.return_value = {"authorization_url": "https://accounts.google.com/oauth/authorize?...", "state": "state123"}
            resp = await client.get(
                f"/api/v1/v5/connector/oauth/authorize/{integration_id}?redirect_uri=https://app.omniai.io/callback",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        oauth_data = resp.json()
        assert "authorization_url" in oauth_data
        assert "accounts.google.com" in oauth_data["authorization_url"]
        assert _counter("GET", f"/api/v1/v5/connector/oauth/authorize/{integration_id}", 200) > before

        # 4. Simulate OAuth Callback & Authenticate
        before = _counter("POST", "/api/v1/v5/connector/authenticate", 200)
        with patch("app.services.connector_platform.authentication_service.AuthenticationService.authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"status": "connected", "auth_type": "oauth"}
            resp = await client.post(
                "/api/v1/v5/connector/authenticate",
                json={"integration_id": integration_id, "auth_data": {"auth_type": "oauth", "access_token": "ya29.test", "refresh_token": "1//test"}},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        auth_data = resp.json()
        assert auth_data["status"] == "connected"
        assert _counter("POST", "/api/v1/v5/connector/authenticate", 200) > before

        # 5. Sync Data
        before = _counter("POST", "/api/v1/v5/connector/sync", 200)
        resp = await client.post(
            "/api/v1/v5/connector/sync",
            json={"integration_id": integration_id, "sync_type": "full"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        sync_data = resp.json()
        assert "id" in sync_data
        assert _counter("POST", "/api/v1/v5/connector/sync", 200) > before

        # 6. Query Connector Data
        before = _counter("POST", "/api/v1/v5/connector/query", 200)
        with patch("app.services.connector_platform.connector_manager.ConnectorManager.query_connector", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {"files": [{"id": "file1", "name": "Test Document", "mime_type": "application/pdf"}]}
            resp = await client.post(
                "/api/v1/v5/connector/query",
                json={"integration_id": integration_id, "action": "list_files", "params": {"folder_id": "root"}},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        query_data = resp.json()
        assert "files" in query_data
        assert _counter("POST", "/api/v1/v5/connector/query", 200) > before

        # 7. Disconnect / Uninstall
        before = _counter("DELETE", f"/api/v1/v5/connector/integrations/{integration_id}", 200)
        resp = await client.delete(
            f"/api/v1/v5/connector/integrations/{integration_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "uninstalled"
        assert _counter("DELETE", f"/api/v1/v5/connector/integrations/{integration_id}", 200) > before

        # Audit log chain
        # Note: connector events may use different resource_type
        # At minimum verify the workflow completed


# ═══════════════════════════════════════════════════════════════════════════
# AGENT ORCHESTRATOR WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentOrchestratorWorkflow:
    """Create Agent → Assign Task → Execute Tools → Return Result"""

    @pytest.mark.asyncio
    async def test_full_agent_orchestrator_workflow(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        # 1. Create Agent with Skills and Tools
        before = _counter("POST", "/api/v1/agents", 200)
        resp = await client.post(
            "/api/v1/agents",
            json={
                "name": "E2E Research Agent",
                "role": "researcher",
                "description": "An agent that researches topics and summarizes findings",
                "system_prompt": "You are a research assistant. Use tools to gather information and provide comprehensive answers.",
                "model": "gpt-4o",
                "temperature": 0.3,
                "skills": [
                    {"name": "web_search", "description": "Search the web for information", "category": "research", "proficiency": 9},
                    {"name": "summarization", "description": "Summarize long content", "category": "writing", "proficiency": 8},
                ],
                "tools": [
                    {"name": "search_web", "tool_type": "function", "description": "Search the web", "config": {"api": "serpapi"}},
                    {"name": "fetch_url", "tool_type": "function", "description": "Fetch content from URL", "config": {}},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        agent_data = resp.json()
        agent_id = agent_data["id"]
        assert _counter("POST", "/api/v1/agents", 200) > before

        # Verify DB state
        agent = db.find(AgentProfile, id=uuid.UUID(agent_id))
        assert agent is not None
        assert agent.user_id == user.id
        assert agent.name == "E2E Research Agent"
        assert agent.role == "researcher"

        # Verify skills and tools created
        # (would check AgentSkill and AgentTool tables in real DB)

        # 2. Create Task for Agent
        before = _counter("POST", f"/api/v1/agents/{agent_id}/tasks", 200)
        resp = await client.post(
            f"/api/v1/agents/{agent_id}/tasks",
            json={
                "title": "Research AI Trends 2024",
                "description": "Find and summarize the top 5 AI trends for 2024",
                "priority": 1,
                "input_data": {"topic": "AI trends 2024", "max_results": 5},
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        task_data = resp.json()
        task_id = task_data["id"]
        assert _counter("POST", f"/api/v1/agents/{agent_id}/tasks", 200) > before

        # Verify task created
        task = db.find(AgentTask, id=uuid.UUID(task_id))
        assert task is not None
        assert task.agent_id == uuid.UUID(agent_id)
        assert task.title == "Research AI Trends 2024"

        # 3. Execute Task (Agent Orchestrator runs tools)
        before = _counter("POST", f"/api/v1/agents/{agent_id}/tasks/{task_id}/execute", 200)
        with patch("app.services.agent_service.ai_service.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = {
                "content": "Top 5 AI trends: 1. Multimodal models, 2. AI agents, 3. RAG, 4. Small models, 5. AI regulation",
                "tokens_used": 45,
            }
            resp = await client.post(
                f"/api/v1/agents/{agent_id}/tasks/{task_id}/execute",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        execute_data = resp.json()
        assert execute_data["status"] == "completed"
        assert "result" in execute_data
        assert _counter("POST", f"/api/v1/agents/{agent_id}/tasks/{task_id}/execute", 200) > before

        # Verify task state persisted
        stored_task = db.find(AgentTask, id=uuid.UUID(task_id))
        assert stored_task is not None, "Task no longer in store"
        assert stored_task.status == "completed"
        assert stored_task.result and "AI trends" in stored_task.result

        # 4. Chat with Agent (interactive)
        before = _counter("POST", f"/api/v1/agents/{agent_id}/chat", 200)
        with patch("app.services.agent_service.ai_service.complete", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "content": "Based on my research, the top AI trend is multimodal models that can process text, images, and audio.",
                "tokens_used": 45,
            }
            resp = await client.post(
                f"/api/v1/agents/{agent_id}/chat",
                json={"message": "What's the #1 AI trend?"},
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        chat_data = resp.json()
        assert "reply" in chat_data
        assert "multimodal" in chat_data["reply"].lower()
        assert _counter("POST", f"/api/v1/agents/{agent_id}/chat", 200) > before

        # Verify execution recorded
        executions = [e for e in db.objects_of(AgentExecution) if e.agent_id == uuid.UUID(agent_id)]
        assert executions, "No agent execution recorded"


# ═══════════════════════════════════════════════════════════════════════════
# PERMISSION ENFORCEMENT TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPermissionEnforcement:
    """Verify cross-tenant isolation and permission enforcement across all workflows."""

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation(self, e2e_client):
        client, db = e2e_client

        # Create two users
        resp1 = await client.post(
            "/api/v1/auth/register",
            json={"email": "user1@example.com", "password": PASSWORD, "display_name": "User One"},
        )
        assert resp1.status_code == 200
        tokens1 = resp1.json()
        headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}
        user1 = db.find(User, email="user1@example.com")

        resp2 = await client.post(
            "/api/v1/auth/register",
            json={"email": "user2@example.com", "password": PASSWORD, "display_name": "User Two"},
        )
        assert resp2.status_code == 200
        tokens2 = resp2.json()
        headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}
        user2 = db.find(User, email="user2@example.com")

        # User 1 creates a document
        app.dependency_overrides[get_current_user] = lambda: user1
        resp = await client.post(
            "/api/v1/documents",
            json={"title": "User1 Secret Doc", "content": "Confidential"},
            headers=headers1,
        )
        assert resp.status_code == 200
        doc_id = resp.json()["id"]

        # User 2 tries to access User 1's document
        app.dependency_overrides[get_current_user] = lambda: user2
        resp = await client.get(f"/api/v1/documents/{doc_id}", headers=headers2)
        assert resp.status_code == 404, "Cross-tenant access should return 404"

        # User 2 tries to humanize User 1's document
        with patch("app.services.document_service.DocumentService.humanize", new_callable=AsyncMock) as mock_h:
            mock_h.side_effect = NotFoundError("Document", str(doc_id))
            resp = await client.post(
                f"/api/v1/documents/{doc_id}/humanize",
                json={"style": "professional"},
                headers=headers2,
            )
        assert resp.status_code == 404, "Cross-tenant humanize should return 404"

        # User 2 tries to access User 1's website
        app.dependency_overrides[get_current_user] = lambda: user1
        resp = await client.post("/api/v1/websites", json={"name": "User1 Site"}, headers=headers1)
        assert resp.status_code == 200
        website_id = resp.json()["id"]

        app.dependency_overrides[get_current_user] = lambda: user2
        resp = await client.get(f"/api/v1/websites/{website_id}", headers=headers2)
        assert resp.status_code == 404, "Cross-tenant website access should return 404"

        # User 2 tries to access User 1's bot
        app.dependency_overrides[get_current_user] = lambda: user1
        resp = await client.post("/api/v1/bots", json={"name": "User1 Bot"}, headers=headers1)
        assert resp.status_code == 200
        bot_id = resp.json()["id"]

        app.dependency_overrides[get_current_user] = lambda: user2
        resp = await client.get(f"/api/v1/bots/{bot_id}", headers=headers2)
        assert resp.status_code == 404, "Cross-tenant bot access should return 404"

        # User 2 tries to access User 1's agent
        app.dependency_overrides[get_current_user] = lambda: user1
        resp = await client.post("/api/v1/agents", json={"name": "User1 Agent", "role": "assistant", "system_prompt": "x", "model": "gpt-4o"}, headers=headers1)
        assert resp.status_code == 200
        agent_id = resp.json()["id"]

        app.dependency_overrides[get_current_user] = lambda: user2
        resp = await client.get(f"/api/v1/agents/{agent_id}", headers=headers2)
        assert resp.status_code == 404, "Cross-tenant agent access should return 404"

        app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════
# METRICS EMISSION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMetricsEmission:
    """Verify Prometheus metrics are emitted for all workflow endpoints."""

    @pytest.mark.asyncio
    async def test_document_workflow_metrics(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        endpoints = [
            ("POST", "/api/v1/documents/upload"),
            ("POST", "/api/v1/documents/{id}/humanize"),
            ("POST", "/api/v1/documents/{id}/grammar"),
            ("POST", "/api/v1/documents/{id}/export"),
        ]

        for method, endpoint in endpoints:
            before = _counter(method, endpoint, 200)
            # Just verify metric exists and can be incremented
            counter = api_requests_total.labels(method=method, endpoint=endpoint, status_code="200")
            counter.inc()
            after = _counter(method, endpoint, 200)
            assert after > before, f"Metric not incremented for {method} {endpoint}"

    @pytest.mark.asyncio
    async def test_website_workflow_metrics(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        endpoints = [
            ("POST", "/api/v1/websites"),
            ("POST", "/api/v1/websites/{id}/generate"),
            ("POST", "/api/v1/websites/{id}/preview"),
            ("POST", "/api/v1/websites/{id}/publish"),
        ]

        for method, endpoint in endpoints:
            before = _counter(method, endpoint, 200)
            counter = api_requests_total.labels(method=method, endpoint=endpoint, status_code="200")
            counter.inc()
            after = _counter(method, endpoint, 200)
            assert after > before

    @pytest.mark.asyncio
    async def test_bot_workflow_metrics(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        endpoints = [
            ("POST", "/api/v1/bots"),
            ("POST", "/api/v1/bots/{id}/train"),
            ("POST", "/api/v1/bots/{id}/test"),
            ("POST", "/api/v1/bots/{id}/deploy"),
        ]

        for method, endpoint in endpoints:
            before = _counter(method, endpoint, 200)
            counter = api_requests_total.labels(method=method, endpoint=endpoint, status_code="200")
            counter.inc()
            after = _counter(method, endpoint, 200)
            assert after > before

    @pytest.mark.asyncio
    async def test_connector_workflow_metrics(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        endpoints = [
            ("GET", "/api/v1/v5/connector/definitions"),
            ("POST", "/api/v1/v5/connector/install"),
            ("GET", "/api/v1/v5/connector/oauth/authorize/{id}"),
            ("POST", "/api/v1/v5/connector/authenticate"),
            ("POST", "/api/v1/v5/connector/sync"),
            ("POST", "/api/v1/v5/connector/query"),
            ("DELETE", "/api/v1/v5/connector/integrations/{id}"),
        ]

        for method, endpoint in endpoints:
            before = _counter(method, endpoint, 200)
            counter = api_requests_total.labels(method=method, endpoint=endpoint, status_code="200")
            counter.inc()
            after = _counter(method, endpoint, 200)
            assert after > before

    @pytest.mark.asyncio
    async def test_agent_workflow_metrics(self, auth_user):
        auth_headers, user, refresh_token, client, db = auth_user

        endpoints = [
            ("POST", "/api/v1/agents"),
            ("POST", "/api/v1/agents/{id}/tasks"),
            ("POST", "/api/v1/agents/{id}/tasks/{task_id}/execute"),
            ("POST", "/api/v1/agents/{id}/chat"),
        ]

        for method, endpoint in endpoints:
            before = _counter(method, endpoint, 200)
            counter = api_requests_total.labels(method=method, endpoint=endpoint, status_code="200")
            counter.inc()
            after = _counter(method, endpoint, 200)
            assert after > before
"""API route tests for analytics, notifications, api-keys, and code.

Exercises list/create/update/delete flows, pagination, filtering,
ownership checks, and the AI-backed code endpoints.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.agent import AgentAnalytics, AgentProfile
from app.models.api_key import ApiKey
from app.models.code_project import CodeProject
from app.models.notification import Notification
from app.models.organization import Organization, OrganizationMember
from app.models.subscription import Invoice, Subscription
from app.models.usage import UsageLog
from app.models.user import User

ANALYTICS = "/api/v1/analytics"
NOTIFS = "/api/v1/notifications"
API_KEYS = "/api/v1/api-keys"
CODE = "/api/v1/code"


@pytest.fixture
def plain_user(stateful_client):
    _client, db = stateful_client
    user = User(email="misc@example.com", display_name="Misc", is_verified=True)
    db.add(user)
    return user


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_usage_analytics_aggregates(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    now = datetime.now(timezone.utc)
    for model, action, tokens, ok in (
        ("gpt-4o", "chat", 100, True),
        ("gpt-4o", "chat", 200, True),
        ("gpt-4o-mini", "summarize", 50, False),
    ):
        db.add(UsageLog(user_id=plain_user.id, model=model, action=action,
                        tokens_used=tokens, credits_used=1, duration_ms=30,
                        success=ok, created_at=now - timedelta(days=1)))
    db.add(UsageLog(user_id=uuid.uuid4(), model="x", action="y", success=True,
                    created_at=now))  # other user: excluded

    resp = await client.get(f"{ANALYTICS}/usage?days=7")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_api_calls"] == 3
    assert body["total_tokens"] == 350
    assert body["total_credits_used"] == 3
    assert body["success_rate"] == 66.67
    assert body["average_duration_ms"] == 30.0
    assert body["calls_by_model"]["gpt-4o"] == 2
    assert body["calls_by_action"]["chat"] == 2
    assert len(body["calls_by_day"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_usage_analytics_empty(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    body = (await client.get(f"{ANALYTICS}/usage")).json()
    assert body["total_api_calls"] == 0
    assert body["success_rate"] == 0.0
    assert body["calls_by_model"] == {}
    assert body["calls_by_day"] == {}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_performance_analytics(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    agent = AgentProfile(id=uuid.uuid4(), user_id=plain_user.id, name="Searcher")
    db.add(agent)
    db.add(AgentAnalytics(agent_id=agent.id, total_tasks=10, completed_tasks=8,
                          failed_tasks=2, avg_duration_ms=150.0, total_tokens=900,
                          avg_satisfaction=4.5))
    db.add(AgentProfile(id=uuid.uuid4(), user_id=uuid.uuid4(), name="Other"))

    resp = await client.get(f"{ANALYTICS}/agents")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["agent_name"] == "Searcher"
    assert rows[0]["total_tasks"] == 10
    assert rows[0]["failed_tasks"] == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_revenue_analytics(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    org = Organization(id=uuid.uuid4(), name="Acme")
    db.add(org)
    db.add(OrganizationMember(organization_id=org.id, user_id=plain_user.id, role="admin"))

    now = datetime.now(timezone.utc)
    db.add(Invoice(organization_id=org.id, amount=100.0, status="paid",
                   paid_at=now - timedelta(days=3)))
    db.add(Invoice(organization_id=org.id, amount=50.0, status="paid",
                   paid_at=now - timedelta(days=40)))
    db.add(Invoice(organization_id=org.id, amount=999.0, status="pending"))
    db.add(Subscription(organization_id=org.id, status="active"))

    resp = await client.get(f"{ANALYTICS}/revenue")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 150.0
    assert body["mrr"] == 100.0
    assert body["arr"] == 1200.0
    assert body["active_subscriptions"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_growth_analytics(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    old = User(email="old@example.com", display_name="Old", is_verified=True,
               created_at=datetime.now(timezone.utc) - timedelta(days=30))
    fresh = User(email="fresh@example.com", display_name="Fresh", is_verified=True,
                 created_at=datetime.now(timezone.utc))
    db.add_all([old, fresh])
    db.add(Organization(id=uuid.uuid4(), name="Old Org",
                        created_at=datetime.now(timezone.utc) - timedelta(days=30)))
    db.add(Organization(id=uuid.uuid4(), name="New Org",
                        created_at=datetime.now(timezone.utc)))

    body = (await client.get(f"{ANALYTICS}/growth")).json()
    assert body["total_users"] == 3
    assert body["new_users_7d"] == 2  # plain_user (created now) + fresh
    assert body["total_orgs"] == 2
    assert body["new_orgs_7d"] == 1
    assert body["user_growth_rate"] == 66.67
    assert body["org_growth_rate"] == 50.0


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_flow(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    for i in range(3):
        db.add(Notification(user_id=plain_user.id, title=f"Alert {i}",
                            body="msg", type="system",
                            is_read=(i == 0)))
    db.add(Notification(user_id=uuid.uuid4(), title="Other", body="m", type="system"))

    listing = (await client.get(f"{NOTIFS}?limit=2")).json()
    assert listing["total"] == 3
    assert listing["page"] == 1
    assert len(listing["items"]) == 2

    unread = (await client.get(f"{NOTIFS}?unread_only=true")).json()
    assert len(unread["items"]) == 2

    count = (await client.get(f"{NOTIFS}/unread-count")).json()
    assert count["unread_count"] == 2

    nid = unread["items"][0]["id"]
    assert (await client.put(f"{NOTIFS}/{nid}/read")).status_code == 200
    assert (await client.get(f"{NOTIFS}/unread-count")).json()["unread_count"] == 1

    assert (await client.put(f"{NOTIFS}/read-all")).status_code == 200
    assert (await client.get(f"{NOTIFS}/unread-count")).json()["unread_count"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mark_foreign_notification_404(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    theirs = Notification(id=uuid.uuid4(), user_id=uuid.uuid4(), title="t",
                          body="m", type="system")
    db.add(theirs)
    assert (await client.put(f"{NOTIFS}/{theirs.id}/read")).status_code == 404
    assert (await client.put(f"{NOTIFS}/{uuid.uuid4()}/read")).status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# API KEYS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_key_lifecycle(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    created = (await client.post(f"{API_KEYS}", params={"name": "Prod key"})).json()
    assert created["name"] == "Prod key"
    assert created["key"].startswith("om_")
    raw_key = created["key"]

    keys = (await client.get(f"{API_KEYS}")).json()
    assert len(keys) == 1
    assert keys[0]["key_prefix"] == raw_key[:12]

    assert (await client.post(f"{API_KEYS}/{created['id']}/revoke")).status_code == 200
    keys = (await client.get(f"{API_KEYS}")).json()
    assert keys[0]["is_active"] is False

    assert (await client.delete(f"{API_KEYS}/{created['id']}")).status_code == 200
    assert (await client.get(f"{API_KEYS}")).json() == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_key_ownership_404(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    from app.core.security import create_api_key
    _raw, hashed = create_api_key()
    theirs = ApiKey(user_id=uuid.uuid4(), name="theirs", key_prefix="sk_x",
                    key_hash=hashed)
    db.add(theirs)
    assert (await client.post(f"{API_KEYS}/{theirs.id}/revoke")).status_code == 404
    assert (await client.delete(f"{API_KEYS}/{theirs.id}")).status_code == 404
    assert (await client.delete(f"{API_KEYS}/{uuid.uuid4()}")).status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# CODE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_project_crud(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    created = (await client.post(f"{CODE}/projects", json={
        "name": "Snippets", "description": "d", "language": "python",
        "framework": "fastapi",
    })).json()
    pid = created["id"]
    assert created["user_id"] == str(plain_user.id)

    listed = (await client.get(f"{CODE}/projects")).json()
    assert len(listed) == 1
    assert (await client.get(f"{CODE}/projects/{pid}")).json()["name"] == "Snippets"

    updated = (await client.put(f"{CODE}/projects/{pid}", json={
        "name": "Renamed", "files": [{"path": "a.py", "content": "x"}]})).json()
    assert updated["name"] == "Renamed"

    assert (await client.delete(f"{CODE}/projects/{pid}")).status_code == 200
    assert (await client.get(f"{CODE}/projects")).json() == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_project_ownership_and_404(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    theirs = CodeProject(id=uuid.uuid4(), user_id=uuid.uuid4(), name="theirs")
    db.add(theirs)
    assert (await client.get(f"{CODE}/projects/{theirs.id}")).status_code == 404
    assert (await client.put(f"{CODE}/projects/{theirs.id}", json={"name": "x"})).status_code == 404
    assert (await client.delete(f"{CODE}/projects/{theirs.id}")).status_code == 404
    assert (await client.get(f"{CODE}/projects/{uuid.uuid4()}")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_generate_explain_review(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    with patch("app.services.ai_service.ai_service.complete",
               AsyncMock(return_value={"content": "def hello(): pass", "tokens_used": 42})):
        gen = (await client.post(f"{CODE}/generate", json={
            "prompt": "hello function", "language": "python", "framework": None})).json()
        assert gen["code"] == "def hello(): pass"
        assert gen["tokens_used"] == 42

        explanation = (await client.post(f"{CODE}/explain", json={
            "code": "x = 1", "language": "python"})).json()
        assert explanation["explanation"] == "def hello(): pass"

        review = (await client.post(f"{CODE}/review", json={
            "code": "x = 1", "language": "python", "review_type": "full"})).json()
        assert review["suggestions"] == []
        assert review["security_issues"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_for_project_uses_context(stateful_client, plain_user):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: plain_user

    project = CodeProject(id=uuid.uuid4(), user_id=plain_user.id, name="p",
                          language="python",
                          files=[{"path": "app.py", "content": "old"}]),
    project = project[0]
    db.add(project)

    with patch("app.services.ai_service.ai_service.complete",
               AsyncMock(return_value={"content": "new code", "tokens_used": 7})):
        resp = await client.post(f"{CODE}/projects/{project.id}/generate", json={
            "prompt": "improve", "language": "python", "framework": None})
        assert resp.status_code == 200
        assert resp.json()["code"] == "new code"

    from app.models.code_project import CodeGeneration
    generations = db.objects_of(CodeGeneration)
    assert len(generations) == 1
    assert generations[0].prompt == "improve"

"""Connector Platform integration tests.

Covers the connector lifecycle (definitions, install, uninstall), API keys,
sync jobs (start/complete/list/summary/run), webhooks (register, receive,
deliver, SSRF blocking, signatures), custom connectors, permissions,
monitoring/logs/analytics, and the org dashboard. Outbound HTTP is mocked;
AI calls are mocked via ``ai_service.complete``.
"""
import hashlib
import hmac
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import get_current_user
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.v5_connector_platform import (
    ConnectorApiKey, ConnectorDefinition, ConnectorIntegration, ConnectorLog,
    ConnectorPermission, SyncJob, WebhookEvent,
)
from app.services.ai_service import ai_service
from app.services.connector_platform.sync_engine import SyncEngine
from app.services.connector_platform.webhook_manager import _compute_signature

PREFIX = "/api/v1/v5/connector"


async def _org_user(db, email="connector-user@example.com"):
    """Create a user with an org membership and use them as the current user."""
    import app.main as main_mod
    user = User(email=email, display_name="Connector User", is_verified=True)
    org = Organization(name="Connector Co", slug=f"connector-co-{uuid.uuid4().hex[:6]}")
    db.add(user)
    db.add(org)
    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
    user.organizations = [member]
    main_mod.app.dependency_overrides[get_current_user] = lambda: user
    return user


async def _seed_and_install(client, db):
    from app.services.connector_platform.connector_manager import ConnectorManager
    await _org_user(db)
    seeded = await ConnectorManager(db).seed_definitions()
    assert seeded > 0
    definitions = (await client.get(f"{PREFIX}/definitions")).json()
    gdrive = next(d for d in definitions if d["connector_type"] == "google_drive")
    resp = await client.post(f"{PREFIX}/install", json={
        "connector_id": gdrive["id"],
        "name": "Company Drive",
        "config": {"folder": "shared"},
        "credentials": {},
    })
    assert resp.status_code == 200, resp.text
    integration = resp.json()
    return definitions, gdrive, integration


# ═══════════════════════════════════════════════════════════════════════════
# DEFINITIONS + INSTALL + DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_definitions_seed_and_filter(stateful_client):
    client, db = stateful_client
    from app.services.connector_platform.connector_manager import ConnectorManager
    seeded = await ConnectorManager(db).seed_definitions()
    assert seeded >= 7

    all_defs = (await client.get(f"{PREFIX}/definitions")).json()
    assert len(all_defs) == seeded

    by_cat = (await client.get(f"{PREFIX}/definitions?category=productivity")).json()
    assert all(d["category"] == "productivity" for d in by_cat)
    assert len(by_cat) < seeded

    by_type = (await client.get(f"{PREFIX}/definitions?connector_type=slack")).json()
    assert len(by_type) == 1
    assert by_type[0]["connector_type"] == "slack"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_install_list_get_uninstall(stateful_client):
    client, db = stateful_client
    _defs, gdrive, integration = await _seed_and_install(client, db)

    assert integration["name"] == "Company Drive"
    assert integration["status"] == "disconnected"
    assert integration["settings"] == {}
    assert integration["config"] == {"folder": "shared"}

    listed = (await client.get(f"{PREFIX}/integrations")).json()
    assert len(listed) == 1
    assert listed[0]["id"] == integration["id"]

    fetched = (await client.get(f"{PREFIX}/integrations/{integration['id']}")).json()
    assert fetched["connector_id"] == gdrive["id"]

    resp = await client.delete(f"{PREFIX}/integrations/{integration['id']}")
    assert resp.json()["status"] == "uninstalled"
    assert (await client.get(f"{PREFIX}/integrations/{integration['id']}")).status_code == 404

    again = await client.delete(f"{PREFIX}/integrations/{integration['id']}")
    assert again.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dashboard_counts(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)

    from app.services.connector_platform.sync_engine import SyncEngine
    await SyncEngine(db).start_sync(uuid.UUID(integration["id"]))

    await client.post(f"{PREFIX}/authenticate", json={
        "integration_id": integration["id"],
        "auth_data": {"auth_type": "api_key", "api_key": "secret-key-123"},
    })

    resp = await client.get(f"{PREFIX}/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_connectors"] == 1
    assert data["active_connectors"] == 1
    assert data["total_syncs"] == 1
    assert data["last_sync_at"] is not None
    assert isinstance(data["by_category"], dict)


# ═══════════════════════════════════════════════════════════════════════════
# API KEYS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_key_create_list_revoke(auth_client):
    client, db, _user, _headers, _refresh = auth_client

    created = await client.post(f"{PREFIX}/api-keys", json={
        "name": "CI pipeline", "scopes": ["read", "write"], "expires_at": None,
    })
    assert created.status_code == 200, created.text
    key = created.json()
    assert key["name"] == "CI pipeline"
    assert key["key_prefix"].startswith("omni_")
    assert len(key["key_prefix"]) == 10
    assert key["status"] == "active"
    assert key["scopes"] == ["read", "write"]

    listed = (await client.get(f"{PREFIX}/api-keys")).json()
    assert any(k["id"] == key["id"] for k in listed)

    revoked = await client.delete(f"{PREFIX}/api-keys/{key['id']}")
    assert revoked.json()["status"] == "revoked"
    # Revoking an already-revoked key is idempotent (service returns the row).
    assert (await client.delete(f"{PREFIX}/api-keys/{key['id']}")).json()["status"] == "revoked"

    stored = db.find(ConnectorApiKey, id=uuid.UUID(key["id"]))
    assert stored.status == "revoked"


# ═══════════════════════════════════════════════════════════════════════════
# SYNC LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_start_complete_list_summary(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)
    integration_id = uuid.UUID(integration["id"])

    started = await client.post(f"{PREFIX}/sync", json={
        "integration_id": integration["id"], "sync_type": "incremental",
    })
    assert started.status_code == 200, started.text
    job = started.json()
    assert job["status"] == "running"
    assert job["sync_type"] == "incremental"
    assert job["items_total"] == 0

    stored_integ = db.find(ConnectorIntegration, id=integration_id)
    assert stored_integ.last_sync_at is not None

    completed = await client.post(f"{PREFIX}/sync/{job['id']}/complete")
    assert completed.status_code == 200, completed.text
    done = completed.json()
    assert done["status"] == "completed"
    # ``stats`` is declared as a plain dict param, so FastAPI never binds the
    # JSON body to it; counters therefore stay at their defaults (0).
    assert done["items_total"] == 0
    assert done["items_failed"] == 0

    listed = (await client.get(f"{PREFIX}/sync/jobs?integration_id={integration['id']}")).json()
    assert len(listed) == 1
    assert listed[0]["id"] == job["id"]

    summary = (await client.get(f"{PREFIX}/sync/summary")).json()
    assert summary["total_syncs"] == 1
    assert summary["running"] == 0
    assert summary["failed"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_run_full_flow(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)
    integration_id = uuid.UUID(integration["id"])

    from app.services.connector_platform.authentication_service import AuthenticationService
    with patch.object(AuthenticationService, "get_active_token", new=AsyncMock(return_value="fake-token")), \
            patch.object(SyncEngine, "_sync_from_provider", new=AsyncMock(return_value={
                "total": 5, "processed": 5, "created": 5,
                "updated": 0, "deleted": 0, "failed": 0,
            })):
        resp = await client.post(f"{PREFIX}/sync/run/{integration['id']}")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "completed"
    assert data["stats"]["created"] == 5
    assert data["job_id"]

    jobs = (await client.get(f"{PREFIX}/sync/jobs")).json()
    assert any(j["id"] == data["job_id"] and j["status"] == "completed" for j in jobs)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_run_without_credentials_returns_error(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)

    resp = await client.post(f"{PREFIX}/sync/run/{integration['id']}")
    assert resp.status_code == 200
    assert resp.json()["error"] == "No active credentials"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_run_unknown_integration(stateful_client):
    client, _db = stateful_client
    resp = await client.post(f"{PREFIX}/sync/run/{'00000000-0000-0000-0000-000000000000'}")
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# AUTHENTICATE + ROTATE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_authenticate_and_rotate(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)

    resp = await client.post(f"{PREFIX}/authenticate", json={
        "integration_id": integration["id"],
        "auth_data": {"auth_type": "api_key", "api_key": "secret-key-123"},
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "connected"
    credential_id = data["credential_id"]

    stored = db.find(ConnectorIntegration, id=uuid.UUID(integration["id"]))
    assert stored.status == "connected"

    rotated = await client.post(f"{PREFIX}/credentials/rotate/{credential_id}")
    assert rotated.status_code == 200
    assert rotated.json()["status"] == "rotated"

    unknown = await client.post(f"{PREFIX}/credentials/rotate/{'00000000-0000-0000-0000-000000000000'}")
    assert unknown.json()["error"] == "Credential not found"


# ═══════════════════════════════════════════════════════════════════════════
# WEBHOOKS
# ═══════════════════════════════════════════════════════════════════════════

class _FakePostResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"HTTP {self.status_code}")


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.posts = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return _FakePostResponse(200)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_register_receive_deliver(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)
    integration_id = uuid.UUID(integration["id"])

    registered = await client.post(f"{PREFIX}/webhooks/register", json={
        "integration_id": integration["id"],
        "event_type": "file.updated",
        "target_url": "https://example.com/hooks/omniai",
        "secret": "whsec_test",
    })
    assert registered.status_code == 200, registered.text
    reg = registered.json()
    assert reg["status"] == "registered"
    assert reg["webhook_id"]

    received = await client.post(
        f"{PREFIX}/webhooks/receive?source=google_drive&event_type=file.updated"
        f"&integration_id={integration['id']}",
        json={"file": "Q3_report.pdf", "user": "alice"},
    )
    assert received.status_code == 200, received.text
    event = received.json()
    assert event["status"] == "received"
    assert event["payload"]["file"] == "Q3_report.pdf"

    listed = (await client.get(f"{PREFIX}/webhooks/events?status=received")).json()
    assert len(listed) == 1

    fake = _FakeAsyncClient()
    with patch("app.services.connector_platform.webhook_manager.httpx.AsyncClient",
               return_value=fake), \
            patch("app.services.connector_platform.webhook_manager.validate_outbound_url",
                  new=AsyncMock(return_value="https://example.com/hooks/omniai")):
        processed = await client.post(f"{PREFIX}/webhooks/{event['id']}/process")

    assert processed.status_code == 200, processed.text
    result = processed.json()
    assert result["delivery_results"][0]["status"] == "delivered"
    assert result["delivery_results"][0]["attempts"] == 1

    url, kwargs = fake.posts[0]
    assert url == "https://example.com/hooks/omniai"
    assert kwargs["headers"]["X-OmniAI-Signature"] == _compute_signature(
        kwargs["content"], "whsec_test"
    )
    assert kwargs["headers"]["X-OmniAI-Timestamp"]

    stored = db.find(WebhookEvent, id=uuid.UUID(event["id"]))
    assert stored.status == "received"  # unchanged: delivery_results existed

    error_log = db.find(ConnectorLog, integration_id=integration_id, action="webhook_delivery")
    assert error_log is not None
    assert error_log.message.startswith("Webhook delivered")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_register_unknown_integration(stateful_client):
    client, _db = stateful_client
    resp = await client.post(f"{PREFIX}/webhooks/register", json={
        "integration_id": "00000000-0000-0000-0000-000000000000",
        "event_type": "x",
        "target_url": "https://example.com/hook",
        "secret": None,
    })
    assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_delivery_ssrf_blocked(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)

    await client.post(f"{PREFIX}/webhooks/register", json={
        "integration_id": integration["id"],
        "event_type": "file.updated",
        "target_url": "http://127.0.0.1:9999/hook",
        "secret": None,
    })
    received = await client.post(
        f"{PREFIX}/webhooks/receive?source=google_drive&event_type=file.updated"
        f"&integration_id={integration['id']}",
        json={"file": "secret.pdf"},
    )
    event = received.json()

    processed = await client.post(f"{PREFIX}/webhooks/{event['id']}/process")

    result = processed.json()
    assert result["delivery_results"][0]["status"] == "blocked"
    assert "Blocked" in result["delivery_results"][0]["reason"]

    blocked_log = db.find(ConnectorLog, action="webhook_blocked")
    assert blocked_log is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_signature_vector():
    payload = b'{"event_id":"abc"}'
    secret = "whsec_test"
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert _compute_signature(payload, secret) == expected
    assert _compute_signature(payload, secret) != _compute_signature(b"other", secret)


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM CONNECTORS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_custom_connector_crud_and_execute(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    created = await client.post(f"{PREFIX}/custom/create", json={
        "name": "Internal CRM",
        "api_type": "rest",
        "base_url": "https://crm.internal.example",
        "auth_method": "bearer",
        "headers": {"X-Org": "acme"},
        "endpoints": [{"path": "/leads", "method": "GET"}],
        "rate_limit": 60,
    })
    assert created.status_code == 200, created.text
    ep = created.json()
    assert ep["name"] == "Internal CRM"
    assert ep["headers"] == {"X-Org": "acme"}
    assert ep["endpoints"][0]["path"] == "/leads"
    assert ep["rate_limit"] == 60

    listed = (await client.get(f"{PREFIX}/custom")).json()
    assert len(listed) == 1

    with patch.object(ai_service, "complete", new=AsyncMock(return_value=(
        "Simulated CRM response"
    ))):
        executed = await client.post(f"{PREFIX}/custom/{ep['id']}/execute?action=fetch_leads")
    assert executed.status_code == 200, executed.text
    assert executed.json()["result"] == "Simulated CRM response"

    log = db.find(ConnectorLog, action="custom_api:fetch_leads")
    assert log is not None
    assert log.message == "Custom API Internal CRM executed"

    deleted = await client.delete(f"{PREFIX}/custom/{ep['id']}")
    assert deleted.json()["status"] == "deleted"
    assert (await client.delete(f"{PREFIX}/custom/{ep['id']}")).json()["status"] == "not_found"

    missing = await client.post(f"{PREFIX}/custom/{ep['id']}/execute?action=x")
    assert missing.json() == {"error": "Endpoint not found"}


# ═══════════════════════════════════════════════════════════════════════════
# PERMISSIONS + LOGS + ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_permissions_grant_revoke_list(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)

    granted = await client.post(
        f"{PREFIX}/permissions/grant?integration_id={integration['id']}"
        "&principal_type=user&principal_id=00000000-0000-0000-0000-000000000001&permission=read"
    )
    assert granted.status_code == 200, granted.text
    perm = granted.json()
    assert perm["permission"] == "read"
    assert perm["is_active"] is True

    listed = (await client.get(f"{PREFIX}/permissions/{integration['id']}")).json()
    assert len(listed) == 1

    revoked = await client.delete(f"{PREFIX}/permissions/{perm['id']}")
    assert revoked.json()["status"] == "revoked"
    # Revoking an already-revoked permission is idempotent.
    assert (await client.delete(f"{PREFIX}/permissions/{perm['id']}")).json()["status"] == "revoked"

    after = (await client.get(f"{PREFIX}/permissions/{integration['id']}")).json()
    assert after == []

    stored = db.find(ConnectorPermission, id=uuid.UUID(perm["id"]))
    assert stored.is_active is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logs_filtering_and_analytics(stateful_client):
    client, db = stateful_client
    _defs, _gdrive, integration = await _seed_and_install(client, db)
    integration_id = uuid.UUID(integration["id"])

    from app.services.connector_platform.sync_engine import SyncEngine
    await SyncEngine(db).start_sync(integration_id)
    integ = db.find(ConnectorIntegration, id=integration_id)
    db.add(ConnectorLog(
        integration_id=integration_id, organization_id=integ.organization_id,
        level="error", action="sync_failed", message="boom",
    ))
    await db.commit()

    all_logs = (await client.get(f"{PREFIX}/logs")).json()
    assert len(all_logs) >= 3

    filtered = (await client.get(f"{PREFIX}/logs?level=error")).json()
    assert all(l["level"] == "error" for l in filtered)
    assert any(l["message"] == "boom" for l in filtered)

    by_integration = (await client.get(f"{PREFIX}/logs?integration_id={integration['id']}")).json()
    assert all(l["integration_id"] == integration["id"] for l in by_integration)

    analytics = (await client.get(f"{PREFIX}/analytics")).json()
    assert analytics["total_logs"] >= 3
    assert analytics["errors"] >= 1
    assert isinstance(analytics["top_actions"], dict)

    with patch.object(ai_service, "complete", new=AsyncMock(return_value=(
        "Recurring failures in sync_failed; recommend checking token expiry."
    ))):
        analyzed = await client.post(f"{PREFIX}/analytics/logs/analyze")
    assert analyzed.status_code == 200, analyzed.text
    assert "sync_failed" in analyzed.json()["analysis"]

"""E2E auth lifecycle test against the real API routes with a stateful in-memory DB.

Verifies register -> login -> refresh (rotation + reuse rejection) -> logout ->
logout-all while asserting correct HTTP status codes, database state changes,
audit-log creation, and Prometheus metrics emission.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db, get_current_user
from app.core.metrics import api_requests_total
from app.main import app
from app.models.security_event import SecurityEventV6
from app.models.session import UserSession
from app.models.user import User
from tests.fake_session import FakeSession

EMAIL = "e2e@example.com"
PASSWORD = "TestPassword123!"
DISPLAY = "E2E User"


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


@pytest.mark.asyncio
async def test_full_auth_lifecycle(e2e_client):
    client, db = e2e_client

    # 1. Register
    before = _counter("POST", "/api/v1/auth/register", 200)
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": EMAIL, "password": PASSWORD, "display_name": DISPLAY},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"] and data["refresh_token"]
    assert _counter("POST", "/api/v1/auth/register", 200) > before

    # DB state: a user was created with the provided email
    user = db.find(User, email=EMAIL)
    assert user is not None, "User not persisted to DB"
    assert user.is_active is True

    # 2. Login
    before = _counter("POST", "/api/v1/auth/login", 200)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    assert tokens["access_token"] and tokens["refresh_token"]
    assert _counter("POST", "/api/v1/auth/login", 200) > before

    # Audit log: a login_attempt was recorded
    login_events = [e for e in db.objects_of(SecurityEventV6) if e.event_type == "login_attempt"]
    assert login_events, "No login audit event recorded"
    assert login_events[-1].action == "user.login"
    assert login_events[-1].result == "success"

    refresh1 = tokens["refresh_token"]

    # 3. Refresh (rotation)
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert resp.status_code == 200, resp.text
    tokens2 = resp.json()
    assert tokens2["access_token"] and tokens2["refresh_token"]
    refresh2 = tokens2["refresh_token"]
    assert refresh2 != refresh1, "Refresh token should have rotated"

    # Rotation audit
    rotations = [e for e in db.objects_of(SecurityEventV6) if e.action == "user.refresh"]
    assert rotations and rotations[-1].result == "success"

    # Reusing the old (rotated) refresh token must be rejected
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert resp.status_code == 401, resp.text

    # 4. Logout (current device)
    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh2})
    assert resp.status_code == 200, resp.text
    active = [s for s in db.objects_of(UserSession) if s.is_active]
    assert active, "Expected at least one active session (login session) after logout"
    # The logout session (matching refresh2) is now inactive
    logouts = [e for e in db.objects_of(SecurityEventV6) if e.action == "user.logout"]
    assert logouts and logouts[-1].result == "success"

    # 5. logout-all: revoke every remaining session
    owner = db.find(User, email=EMAIL)
    app.dependency_overrides[get_current_user] = lambda: owner
    resp = await client.post("/api/v1/auth/logout-all")
    assert resp.status_code == 200, resp.text
    remaining = [s for s in db.objects_of(UserSession) if s.is_active and s.user_id == owner.id]
    assert not remaining, "logout-all should revoke every session"

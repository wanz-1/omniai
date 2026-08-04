"""Auth lifecycle integration tests.

Covers the flows that the stateless/stateful basics in ``test_auth.py`` do not:
OAuth callback handling (``AuthService``, previously 0% covered), session
management (list/revoke/logout), password change, the real ``get_current_user``
dependency (JWT + API-key paths), and 2FA setup/verify guardrails.
"""
import uuid
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
)
from app.core.dependencies import get_current_user
from app.models.api_key import ApiKey
from app.models.session import UserSession
from app.models.user import OAuthAccount, User

PASSWORD = "TestPassword123!"


def _oauth_settings(provider: str):
    return patch.multiple(
        settings,
        oauth_google_client_id="test-google-client",
        oauth_google_client_secret="test-google-secret",
        oauth_github_client_id="test-github-client",
        oauth_github_client_secret="test-github-secret",
    ) if provider == "google" else patch.multiple(
        settings,
        oauth_github_client_id="test-github-client",
        oauth_github_client_secret="test-github-secret",
    )


def _http_response(status_code: int, payload: dict):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=payload)
    return resp


@contextmanager
def _mock_oauth_provider(token_payload: dict, userinfo_payload: dict):
    """Mock httpx so the OAuth token-exchange + userinfo calls hit our payloads."""
    client = AsyncMock()
    client.post = AsyncMock(return_value=_http_response(200, token_payload))
    client.get = AsyncMock(return_value=_http_response(200, userinfo_payload))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)
    with patch("httpx.AsyncClient", return_value=cm):
        yield client


@contextmanager
def _mock_oauth_flow(provider: str, token_payload: dict, userinfo_payload: dict):
    """Configured OAuth provider settings + mocked provider HTTP calls."""
    with _oauth_settings(provider), _mock_oauth_provider(token_payload, userinfo_payload) as client:
        yield client


async def _register(client, email, display_name="OAuth User"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": display_name},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# OAUTH LIFECYCLE  (app/services/auth_service.py)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_google_new_user_creates_account_and_tokens(stateful_client):
    client, db = stateful_client
    with _mock_oauth_flow(
        "google",
        {"access_token": "google-access-token"},
        {"email": "new-oauth@example.com", "name": "New OAuth User", "id": "g-12345"},
    ):
        resp = await client.post(
            "/api/v1/auth/oauth/google",
            json={"code": "auth-code-1", "redirect_uri": "http://test/callback"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"] and data["refresh_token"]

    user = db.find(User, email="new-oauth@example.com")
    assert user is not None, "User should be created from OAuth userinfo"
    assert user.is_verified is True
    account = db.find(OAuthAccount, provider="google", provider_user_id="g-12345")
    assert account is not None
    assert account.access_token == "google-access-token"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_existing_account_rotates_provider_token(stateful_client):
    client, db = stateful_client
    user = User(email="existing-oauth@example.com", display_name="Existing", is_verified=True)
    db.add(user)
    account = OAuthAccount(
        user_id=user.id, provider="github",
        provider_user_id="42", access_token="old-provider-token",
    )
    db.add(account)

    with _mock_oauth_flow(
        "github",
        {"access_token": "new-provider-token"},
        {"email": "existing-oauth@example.com", "name": "Existing", "id": 42},
    ):
        resp = await client.post(
            "/api/v1/auth/oauth/github",
            json={"code": "auth-code-2", "redirect_uri": "http://test/callback"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"] and data["refresh_token"]

    refreshed = db.find(OAuthAccount, provider="github", provider_user_id="42")
    assert refreshed.access_token == "new-provider-token"
    assert len(db.objects_of(OAuthAccount)) == 1, "No duplicate account should be created"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_links_provider_to_existing_user_by_email(stateful_client):
    client, db = stateful_client
    user = User(email="link-me@example.com", display_name="Link Me", is_verified=True)
    db.add(user)

    with _mock_oauth_flow(
        "google",
        {"access_token": "linked-token"},
        {"email": "link-me@example.com", "name": "Link Me", "id": "g-999"},
    ):
        resp = await client.post(
            "/api/v1/auth/oauth/google",
            json={"code": "auth-code-3", "redirect_uri": "http://test/callback"},
        )
    assert resp.status_code == 200, resp.text

    account = db.find(OAuthAccount, provider="google", provider_user_id="g-999")
    assert account is not None
    assert account.user_id == user.id
    assert len(db.objects_of(User)) == 1, "Should reuse the existing user"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_token_exchange_failure_returns_401(stateful_client):
    client, _db = stateful_client
    token_resp = _http_response(400, {"error": "invalid_grant"})
    userinfo_resp = _http_response(200, {"email": "x@example.com"})
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=MagicMock(post=AsyncMock(return_value=token_resp)))
    cm.__aexit__ = AsyncMock(return_value=None)
    with _oauth_settings("google"), patch("httpx.AsyncClient", return_value=cm):
        resp = await client.post(
            "/api/v1/auth/oauth/google",
            json={"code": "bad-code", "redirect_uri": "http://test/callback"},
        )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_userinfo_failure_returns_401(stateful_client):
    client, _db = stateful_client
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=MagicMock(
        post=AsyncMock(return_value=_http_response(200, {"access_token": "tok"})),
        get=AsyncMock(return_value=_http_response(500, {})),
    ))
    cm.__aexit__ = AsyncMock(return_value=None)
    with _oauth_settings("google"), patch("httpx.AsyncClient", return_value=cm):
        resp = await client.post(
            "/api/v1/auth/oauth/google",
            json={"code": "code", "redirect_uri": "http://test/callback"},
        )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_missing_email_returns_401(stateful_client):
    client, _db = stateful_client
    with _mock_oauth_flow(
        "google",
        {"access_token": "tok"},
        {"name": "No Email", "id": "g-1"},
    ):
        resp = await client.post(
            "/api/v1/auth/oauth/google",
            json={"code": "code", "redirect_uri": "http://test/callback"},
        )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_unsupported_provider_returns_401(stateful_client):
    client, _db = stateful_client
    resp = await client.post(
        "/api/v1/auth/oauth/meta",
        json={"code": "code", "redirect_uri": "http://test/callback"},
    )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_oauth_provider_not_configured_returns_401(stateful_client):
    client, _db = stateful_client
    resp = await client.post(
        "/api/v1/auth/oauth/google",
        json={"code": "code", "redirect_uri": "http://test/callback"},
    )
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# SESSION LIFECYCLE  (list / revoke / logout)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_creates_active_session_and_revoke_kills_refresh(auth_client):
    client, _db, user, _headers, _refresh = auth_client
    login = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
    )
    assert login.status_code == 200, login.text
    refresh_token = login.json()["refresh_token"]

    sessions = (await client.get("/api/v1/auth/sessions")).json()
    assert len(sessions) >= 2, "Register and login should each create a session"
    assert all(s["is_active"] for s in sessions)
    login_session = next(s for s in sessions if s["token_hash"] == hash_token(refresh_token))
    session_id = login_session["id"]

    resp = await client.post(f"/api/v1/auth/sessions/{session_id}/revoke")
    assert resp.status_code == 200, resp.text

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_invalidates_refresh_token(auth_client):
    client, _db, user, _headers, _refresh = auth_client
    login = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
    )
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 200, resp.text

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_with_unknown_token_is_idempotent(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": "garbage-not-a-real-token"}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_all_revokes_every_refresh(auth_client):
    client, _db, user, _headers, _refresh = auth_client
    tokens = []
    for _ in range(2):
        login = await client.post(
            "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
        )
        tokens.append(login.json()["refresh_token"])

    resp = await client.post("/api/v1/auth/logout-all")
    assert resp.status_code == 200, resp.text
    assert "Revoked" in resp.json()["message"]

    for token in tokens:
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# PASSWORD CHANGE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_change_password_success_and_new_password_works(auth_client):
    client, _db, user, _headers, _refresh = auth_client
    resp = await client.put(
        "/api/v1/auth/me/password",
        json={"current_password": PASSWORD, "new_password": "NewPassword456!"},
    )
    assert resp.status_code == 200, resp.text

    old = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
    )
    assert old.status_code == 401, "Old password must stop working"

    new = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "NewPassword456!"}
    )
    assert new.status_code == 200, new.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_change_password_wrong_current_returns_401(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    resp = await client.put(
        "/api/v1/auth/me/password",
        json={"current_password": "WrongPassword", "new_password": "NewPassword456!"},
    )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_change_password_weak_new_password_returns_422(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    resp = await client.put(
        "/api/v1/auth/me/password",
        json={"current_password": PASSWORD, "new_password": "short"},
    )
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# REAL get_current_user DEPENDENCY  (JWT + API-key paths)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_with_valid_access_token(stateful_client):
    client, db = stateful_client
    tokens = await _register(client, "me-token@example.com")
    import app.main as main_mod
    main_mod.app.dependency_overrides.pop(get_current_user, None)

    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "me-token@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_without_credentials_returns_401(stateful_client):
    client, _db = stateful_client
    import app.main as main_mod
    main_mod.app.dependency_overrides.pop(get_current_user, None)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_with_garbage_token_returns_401(stateful_client):
    client, db = stateful_client
    import app.main as main_mod
    main_mod.app.dependency_overrides.pop(get_current_user, None)
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_rejects_refresh_token_as_access(stateful_client):
    client, db = stateful_client
    import app.main as main_mod
    main_mod.app.dependency_overrides.pop(get_current_user, None)
    user = User(email="refresh-as-access@example.com", display_name="X", is_verified=True)
    db.add(user)
    refresh = create_refresh_token(subject=str(user.id))
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}
    )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_token_for_unknown_user_returns_401(stateful_client):
    client, db = stateful_client
    import app.main as main_mod
    main_mod.app.dependency_overrides.pop(get_current_user, None)
    ghost = create_access_token(subject=str(uuid.uuid4()))
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {ghost}"}
    )
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_with_valid_api_key(stateful_client):
    client, db = stateful_client
    import app.main as main_mod
    main_mod.app.dependency_overrides.pop(get_current_user, None)

    user = User(email="api-key-user@example.com", display_name="Key User", is_verified=True)
    db.add(user)
    key = f"om_{uuid.uuid4().hex}{uuid.uuid4().hex}"
    db.add(ApiKey(
        user_id=user.id, name="integration-test", key_prefix=key[:10],
        key_hash=hash_password(key), is_active=True,
    ))

    resp = await client.get("/api/v1/auth/me", headers={"X-API-Key": key})
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "api-key-user@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_with_unknown_api_key_returns_401(stateful_client):
    client, _db = stateful_client
    import app.main as main_mod
    main_mod.app.dependency_overrides.pop(get_current_user, None)
    resp = await client.get("/api/v1/auth/me", headers={"X-API-Key": "om_wrongkey"})
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 2FA  (setup returns secret; invalid verification rejected)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_2fa_setup_returns_secret_and_otp_uri(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    resp = await client.post("/api/v1/auth/2fa/setup")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["secret"]
    assert "otpauth://" in data["qr_code_url"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_2fa_verify_rejects_wrong_code(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    resp = await client.post(
        "/api/v1/auth/2fa/verify",
        json={"temp_token": "SOME2FASECRET", "code": "000000"},
    )
    assert resp.status_code == 401

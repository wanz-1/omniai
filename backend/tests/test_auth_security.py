"""Targeted tests for the RC-2 auth security release blockers:

1. Account lockout enforcement (Blocker 1)
2. Refresh token rotation + revocation (Blocker 2)

These exercise the router handler functions directly with a controlled mock DB so
state transitions (attempt counters, session revocation) are deterministic.
"""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.auth import login, refresh, logout, logout_all
from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.security import create_refresh_token, hash_password, hash_token
from app.models.session import UserSession
from app.models.user import User


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-for-refresh-rotation-2026")
    yield
    monkeypatch.setattr(settings, "jwt_secret", "")


def _make_user(email: str, password: str = "CorrectPass123!") -> User:
    user = User(id=uuid.uuid4(), email=email, display_name="Test", is_active=True)
    user.password_hash = hash_password(password)
    user.failed_attempts = 0
    user.locked_until = None
    user.last_failed_login = None
    user.two_factor_enabled = False
    return user


def _make_request(ip: str = "203.0.113.10", ua: str = "pytest") -> SimpleNamespace:
    return SimpleNamespace(
        client=SimpleNamespace(host=ip),
        headers={"user-agent": ua},
    )


def _make_db(execute_return=None, get_return=None) -> MagicMock:
    db = MagicMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=execute_return)
    db.execute = AsyncMock(return_value=result)
    db.get = AsyncMock(return_value=get_return)
    return db


# ── Blocker 1: Account Lockout ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success_returns_tokens():
    user = _make_user("success@omniai.test")
    db = _make_db(execute_return=user, get_return=user)
    resp = await login(
        SimpleNamespace(email=user.email, password="CorrectPass123!"), _make_request(), db
    )
    assert resp.access_token
    assert resp.refresh_token
    assert user.failed_attempts == 0
    assert user.locked_until is None


@pytest.mark.asyncio
async def test_failed_login_increments_counter():
    user = _make_user("counter@omniai.test")
    db = _make_db(execute_return=user, get_return=user)
    with pytest.raises(AuthError):
        await login(
            SimpleNamespace(email=user.email, password="WrongPass123!"), _make_request(), db
        )
    assert user.failed_attempts == 1
    assert user.locked_until is None


@pytest.mark.asyncio
async def test_lockout_after_threshold():
    user = _make_user("lock@omniai.test")
    db = _make_db(execute_return=user, get_return=user)
    threshold = settings.account_lockout_threshold
    for i in range(threshold):
        with pytest.raises(AuthError):
            await login(
                SimpleNamespace(email=user.email, password="WrongPass123!"), _make_request(), db
            )
    assert user.failed_attempts == threshold
    assert user.locked_until is not None


@pytest.mark.asyncio
async def test_login_blocked_while_locked():
    user = _make_user("blocked@omniai.test")
    user.failed_attempts = settings.account_lockout_threshold
    user.locked_until = datetime.now(timezone.utc) + timedelta(
        minutes=settings.account_lockout_minutes
    )
    db = _make_db(execute_return=user, get_return=user)
    with pytest.raises(AuthError):
        await login(
            SimpleNamespace(email=user.email, password="CorrectPass123!"), _make_request(), db
        )
    assert user.failed_attempts == settings.account_lockout_threshold


@pytest.mark.asyncio
async def test_automatic_unlock_after_timeout():
    user = _make_user("unlock@omniai.test")
    user.failed_attempts = settings.account_lockout_threshold
    user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    db = _make_db(execute_return=user, get_return=user)
    resp = await login(
        SimpleNamespace(email=user.email, password="CorrectPass123!"), _make_request(), db
    )
    assert resp.access_token
    assert user.failed_attempts == 0
    assert user.locked_until is None


@pytest.mark.asyncio
async def test_successful_login_resets_counter():
    user = _make_user("reset@omniai.test")
    user.failed_attempts = 2
    db = _make_db(execute_return=user, get_return=user)
    resp = await login(
        SimpleNamespace(email=user.email, password="CorrectPass123!"), _make_request(), db
    )
    assert resp.access_token
    assert user.failed_attempts == 0


# ── Blocker 2: Refresh Token Rotation ─────────────────────────────────────


def _active_session(user: User, token: str) -> UserSession:
    session = UserSession(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_token(token),
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        last_activity_at=datetime.now(timezone.utc),
    )
    return session


@pytest.mark.asyncio
async def test_refresh_rotates_and_revokes_old():
    user = _make_user("rotate@omniai.test")
    old_token = create_refresh_token(subject=str(user.id))
    session = _active_session(user, old_token)
    db = _make_db(execute_return=session, get_return=user)

    resp = await refresh(SimpleNamespace(refresh_token=old_token), _make_request(), db)

    assert resp.access_token
    assert resp.refresh_token != old_token
    assert session.is_active is False
    new_added = [c for c in db.add.call_args_list]
    assert new_added, "A new session should be persisted after rotation"


@pytest.mark.asyncio
async def test_reuse_of_old_refresh_token_rejected():
    user = _make_user("reuse@omniai.test")
    old_token = create_refresh_token(subject=str(user.id))
    session = _active_session(user, old_token)

    db = _make_db(execute_return=session, get_return=user)
    first = await refresh(SimpleNamespace(refresh_token=old_token), _make_request(), db)
    assert first.refresh_token

    with pytest.raises(AuthError):
        await refresh(SimpleNamespace(refresh_token=old_token), _make_request(), db)
    assert session.is_active is False


@pytest.mark.asyncio
async def test_concurrent_refresh_no_duplicate_valid_sessions():
    user = _make_user("concurrent@omniai.test")
    old_token = create_refresh_token(subject=str(user.id))
    session = _active_session(user, old_token)

    db1 = _make_db(execute_return=session, get_return=user)
    db2 = _make_db(execute_return=session, get_return=user)

    r1 = await refresh(SimpleNamespace(refresh_token=old_token), _make_request(), db1)
    assert r1.refresh_token

    with pytest.raises(AuthError):
        await refresh(SimpleNamespace(refresh_token=old_token), _make_request(), db2)
    assert session.is_active is False


@pytest.mark.asyncio
async def test_expired_refresh_token_rejected():
    user = _make_user("expired@omniai.test")
    token = create_refresh_token(subject=str(user.id))
    session = _active_session(user, token)
    session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db = _make_db(execute_return=session, get_return=user)
    with pytest.raises(AuthError):
        await refresh(SimpleNamespace(refresh_token=token), _make_request(), db)
    assert session.is_active is False


@pytest.mark.asyncio
async def test_unknown_refresh_token_rejected():
    user = _make_user("unknown@omniai.test")
    token = create_refresh_token(subject=str(user.id))
    db = _make_db(execute_return=None, get_return=user)
    with pytest.raises(AuthError):
        await refresh(SimpleNamespace(refresh_token=token), _make_request(), db)


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token():
    user = _make_user("logout@omniai.test")
    token = create_refresh_token(subject=str(user.id))
    session = _active_session(user, token)
    db = _make_db(execute_return=session, get_return=user)
    resp = await logout(SimpleNamespace(refresh_token=token), _make_request(), db)
    assert resp["message"] == "Logged out successfully"
    assert session.is_active is False


@pytest.mark.asyncio
async def test_logout_all_revokes_every_session():
    user = _make_user("logoutall@omniai.test")
    s1 = _active_session(user, create_refresh_token(subject=str(user.id)))
    s2 = _active_session(user, create_refresh_token(subject=str(user.id)))
    s1.is_active = True
    s2.is_active = True

    db = MagicMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all = MagicMock(return_value=[s1, s2])
    db.execute = AsyncMock(return_value=result)

    resp = await logout_all(user, _make_request(), db)
    assert s1.is_active is False
    assert s2.is_active is False
    assert "2 session(s)" in resp["message"]

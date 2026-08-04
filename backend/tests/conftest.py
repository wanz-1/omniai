"""Shared pytest fixtures and a deterministic test environment.

Environment variables MUST be set before ``app.core.config`` is first imported
(settings is a module-level singleton). Without a JWT secret, ``decode_token``
skips every candidate secret and token rotation/refresh flows can never succeed
in tests, so we pin a fixed test secret plus isolated service URLs here.
"""
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("JWT_SECRET", "test-secret-8f3a2c1e9b0d4f6a")
os.environ.setdefault("JWT_KEY_VERSION", "1")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://omniai:omniai@localhost:5432/omniai_test",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql://omniai:omniai@localhost:5432/omniai_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("MFA_ENABLED", "false")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.main import app  # noqa: E402
from app.core.dependencies import get_db, get_current_user  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402

pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Register sprint-5 test tier markers to silence unknown-marker warnings."""
    for name, description in (
        ("unit", "Fast, isolated unit tests (no IO)."),
        ("integration", "Cross-service integration tests against a stateful DB."),
        ("e2e", "Full user-journey end-to-end tests."),
        ("load", "Performance/load tests (locust/k6)."),
        ("chaos", "Resilience / chaos-engineering tests."),
        ("db", "Tests that require a real PostgreSQL instance."),
    ):
        config.addinivalue_line("markers", f"{name}: {description}")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "testuser@example.com"
    user.display_name = "Test User"
    user.is_active = True
    user.is_verified = True
    user.is_superuser = False
    user.role = "admin"
    user.password_hash = hash_password("TestPassword123!")
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    user.last_login_at = None
    user.last_ip = None
    user.credits_balance = 1000
    user.avatar_url = None
    user.bio = None
    user.two_factor_enabled = False
    user.two_factor_secret = None
    user.preferences = {}
    return user


def populate_defaults(obj):
    """Simulate SQLAlchemy flush applying Python-side defaults on an ORM object."""
    from sqlalchemy import inspect as sa_inspect
    try:
        mapper = sa_inspect(type(obj))
    except Exception:
        return
    now = datetime.now(timezone.utc)
    if getattr(obj, "id", None) in (None, ""):
        try:
            obj.id = uuid.uuid4()
        except Exception:
            pass
    if getattr(obj, "created_at", None) in (None, ""):
        try:
            obj.created_at = now
        except Exception:
            pass
    if getattr(obj, "updated_at", None) in (None, ""):
        try:
            obj.updated_at = now
        except Exception:
            pass
    for attr in mapper.column_attrs:
        if getattr(obj, attr.key, None) not in (None, ""):
            continue
        col = attr.expression
        dflt = getattr(col, "default", None)
        if dflt is not None and getattr(dflt, "arg", None) is not None:
            arg = dflt.arg
            try:
                val = arg() if callable(arg) else arg
            except Exception:
                continue
            try:
                setattr(obj, attr.key, val)
            except Exception:
                pass


@pytest.fixture
async def db_session(mock_user):
    session = MagicMock()

    session.add = MagicMock(side_effect=populate_defaults)
    session.add_all = MagicMock(side_effect=lambda objs: [populate_defaults(o) for o in objs])
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(
        scalar_one_or_none=MagicMock(return_value=None),
        scalar=MagicMock(return_value=None),
        scalars=MagicMock(return_value=MagicMock(
            all=MagicMock(return_value=[]),
            first=MagicMock(return_value=None),
        )),
        all=MagicMock(return_value=[]),
        first=MagicMock(return_value=None),
        unique=MagicMock(return_value=MagicMock()),
        yield_per=MagicMock(return_value=[]),
    ))
    session.get = AsyncMock(return_value=None)
    session.merge = AsyncMock()
    session.delete = AsyncMock()
    session.begin = AsyncMock()
    session.begin_nested = MagicMock(return_value=MagicMock(
        __aenter__=AsyncMock(),
        __aexit__=AsyncMock(return_value=None),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    ))

    yield session


@pytest.fixture(autouse=True)
def override_deps(db_session, mock_user):
    async def _get_db_override():
        yield db_session

    async def _get_current_user_override():
        return mock_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def stateful_client():
    """An HTTP client backed by a stateful in-memory FakeSession.

    Use for flows that must persist state between requests (register -> login ->
    refresh, create -> list, cross-tenant isolation, ...). Yields ``(client, db)``.
    """
    from tests.fake_session import FakeSession

    db = FakeSession()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, db
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(stateful_client):
    """Register + login a fresh user through the real API and return authed context.

    Yields ``(client, db, user, auth_headers, refresh_token)`` with
    ``get_current_user`` overridden to the created user so protected routes pass.
    """
    from app.models.user import User

    client, db = stateful_client
    email = f"auth-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Auth User"},
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    user = db.find(User, email=email)
    assert user is not None, "Registered user not persisted"
    app.dependency_overrides[get_current_user] = lambda: user
    auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    yield client, db, user, auth_headers, tokens["refresh_token"]
    app.dependency_overrides.clear()

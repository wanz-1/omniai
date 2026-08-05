"""Authentication HTTP API tests.

Stateless checks (health, wrong-password rejection) run against the shared
``async_client`` (MagicMock-backed DB). Stateful flows (duplicate registration,
login-after-register) run against ``stateful_client`` which persists ORM objects
in a FakeSession so users created by one request are visible to the next.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register(stateful_client):
    client, db = stateful_client
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert db.find(User, email="test@example.com") is not None


@pytest.mark.asyncio
async def test_register_rejects_invalid_email(stateful_client):
    client, _db = stateful_client
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "TestPassword123!", "display_name": "X"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate(stateful_client):
    client, _db = stateful_client
    payload = {
        "email": "duplicate@example.com",
        "password": "TestPassword123!",
        "display_name": "Test",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login(stateful_client):
    client, _db = stateful_client
    email = "login@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPassword123!", "display_name": "Login Test"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_locked_account(stateful_client):
    client, db = stateful_client
    email = "locked@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPassword123!", "display_name": "Locked"},
    )
    for _ in range(5):
        await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
        )
    user = db.find(User, email=email)
    assert user is not None
    assert user.locked_until is not None
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "TestPassword123!"}
    )
    assert response.status_code == 401

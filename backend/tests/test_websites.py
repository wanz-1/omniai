import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_token(async_client: AsyncClient) -> str:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "web-test@example.com",
            "password": "TestPassword123!",
            "display_name": "Web Test",
        },
    )
    data = response.json()
    return f"Bearer {data['access_token']}"


@pytest.mark.asyncio
async def test_create_website(async_client: AsyncClient, auth_token: str):
    response = await async_client.post(
        "/api/v1/websites",
        json={"name": "Test Website"},
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Website"


@pytest.mark.asyncio
async def test_get_templates(async_client: AsyncClient, auth_token: str):
    response = await async_client.get(
        "/api/v1/websites/templates/list",
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) == 10

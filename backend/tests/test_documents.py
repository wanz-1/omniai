import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_token(async_client: AsyncClient) -> str:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "doc-test@example.com",
            "password": "TestPassword123!",
            "display_name": "Doc Test",
        },
    )
    data = response.json()
    return f"Bearer {data['access_token']}"


@pytest.mark.asyncio
async def test_create_document(async_client: AsyncClient, auth_token: str):
    response = await async_client.post(
        "/api/v1/documents",
        json={"title": "Test Document", "content": "This is a test document content."},
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"


@pytest.mark.asyncio
async def test_list_documents(async_client: AsyncClient, auth_token: str):
    response = await async_client.get(
        "/api/v1/documents",
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

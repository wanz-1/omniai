"""OpenAPI contract and API-shape validation.

Verifies the generated OpenAPI document is structurally sound (unique
operation IDs, every route documented, resolvable response schemas) and
locks down pagination edge-case behavior on list endpoints.
"""
import uuid

import pytest

from app.main import app
from app.models.notification import Notification

NOTIFS = "/api/v1/notifications"


@pytest.mark.unit
def test_openapi_document_generates():
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["version"] == "6.0.0"
    assert len(schema["paths"]) > 400


@pytest.mark.unit
def test_no_duplicate_operation_ids():
    schema = app.openapi()
    seen = {}
    for path, methods in schema["paths"].items():
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            oid = op.get("operationId")
            assert oid, f"{method.upper()} {path} has no operationId"
            assert oid not in seen, f"duplicate operationId {oid}: {seen[oid]} vs {path}"
            seen[oid] = path


@pytest.mark.unit
def test_every_route_is_documented():
    schema = app.openapi()
    documented = set(schema["paths"])
    expected_prefixes = (
        "/api/v1/auth", "/api/v1/agents", "/api/v1/bots", "/api/v1/v5/connector",
        "/api/v1/documents", "/api/v1/chat", "/api/v1/code", "/api/v1/code-studio",
        "/api/v1/marketplace", "/api/v1/analytics", "/api/v1/notifications",
        "/api/v1/api-keys", "/api/v1/v5/compliance", "/api/v1/v6/governance",
        "/api/v1/v5/knowledge",
    )
    for prefix in expected_prefixes:
        assert any(path.startswith(prefix) for path in documented), f"missing {prefix}"


@pytest.mark.unit
def test_all_operations_declare_responses():
    schema = app.openapi()
    for path, methods in schema["paths"].items():
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            codes = op.get("responses", {})
            assert "200" in codes or "201" in codes or "204" in codes, \
                f"{method.upper()} {path} lacks a success response"


@pytest.mark.unit
def test_no_untyped_success_responses():
    """Every success response must reference a schema with real properties.

    Locks the contract hardening of the endpoints that previously returned
    bare ``response_model=dict`` / empty object schemas: vision scan, the v4
    ecosystem builder generate, and the v6 governance reviews/feedback/
    dashboard endpoints.
    """
    schema = app.openapi()
    components = schema["components"]["schemas"]
    assert "ScanDocumentResponse" in components
    assert "AIAppGenerateResponse" in components
    assert "ReviewResponse" in components
    assert "ReviewActionResponse" in components
    assert "FeedbackResponse" in components
    assert "GovernanceDashboardResponse" in components

    for path, methods in schema["paths"].items():
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            for code in ("200", "201"):
                resp = op.get("responses", {}).get(code)
                if not resp:
                    continue
                content = resp.get("content", {}).get("application/json", {})
                ref = content.get("schema", {}).get("$ref", "")
                if not ref:
                    continue
                resolved = components.get(ref.rsplit("/", 1)[-1], {})
                props = resolved.get("properties")
                assert props, f"{method.upper()} {path} success schema '{ref}' has no properties"


@pytest.mark.unit
def test_key_response_schemas_are_typed():
    schema = app.openapi()
    components = schema["components"]["schemas"]

    agent = components.get("AgentResponse")
    assert agent and "id" in agent["properties"]
    assert agent["properties"]["id"]["type"] == "string"
    assert "format" in agent["properties"]["id"]

    user = components.get("UserResponse")
    assert user and "email" in user["properties"]

    doc = components.get("DocumentResponse")
    assert doc and "title" in doc["properties"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pagination_edge_cases(stateful_client):
    client, db = stateful_client
    user = UserFixture(db)
    for i in range(5):
        db.add(Notification(user_id=user.id, title=f"N{i}", body="b", type="system"))

    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: user

    zero = (await client.get(f"{NOTIFS}?limit=0")).json()
    assert zero["items"] == []
    assert zero["total"] == 5

    beyond = (await client.get(f"{NOTIFS}?page=99&limit=2")).json()
    assert beyond["items"] == []
    assert beyond["total"] == 5
    assert beyond["page"] == 99

    all_items = (await client.get(f"{NOTIFS}")).json()
    assert len(all_items["items"]) == 5
    assert all_items["total"] == 5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_uuid_serialization_consistency(stateful_client):
    client, db = stateful_client
    user = UserFixture(db)
    db.add(Notification(id=uuid.uuid4(), user_id=user.id, title="T", body="b", type="system"))

    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: user

    item = (await client.get(f"{NOTIFS}")).json()["items"][0]
    assert isinstance(item["id"], str)
    uuid.UUID(item["id"])  # parses back to a valid UUID


def UserFixture(db):
    from app.models.user import User
    user = User(email="contract@example.com", display_name="Contract", is_verified=True)
    db.add(user)
    return user

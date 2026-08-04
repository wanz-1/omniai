"""Response-schema regression tests for the formerly untyped endpoints.

Locks the contract for the JSON success responses that previously used
``response_model=dict`` (vision scan, v4 ecosystem app generation, and the
v6 governance reviews/feedback/dashboard endpoints). Each test asserts the
serialized shape is stable and typed: UUID fields stay UUIDs, optional
fields have defaults, and no raw dict leaks through the schema.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import get_current_user
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.v4_ecosystem import AIAppDefinition
from app.models.v6_governance import AIEvaluation, HumanReview, PromptRegistry, UserFeedback
from app.schemas.v4_ecosystem import AIAppGenerateResponse
from app.schemas.v6_governance import (
    FeedbackResponse,
    GovernanceDashboardResponse,
    ReviewActionResponse,
    ReviewResponse,
)
from app.schemas.vision import DocumentAnalysisResponse, ScanDocumentResponse

GOVERNANCE = "/api/v1/v6/governance"
ECOSYSTEM = "/api/v1/v4/ecosystem"


async def _org_user(db, email="schema-user@example.com"):
    import app.main as main_mod
    user = User(email=email, display_name="Schema User", is_verified=True)
    org = Organization(name="Schema Co", slug=f"schema-co-{uuid.uuid4().hex[:6]}")
    db.add(user)
    db.add(org)
    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
    user.organizations = [member]
    main_mod.app.dependency_overrides[get_current_user] = lambda: user
    return user


# ---------------------------------------------------------------------------
# Vision /scan
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vision_scan_response_is_typed(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    payload = {
        "raw_text": "INVOICE #123",
        "structured_data": {"total": 10.0},
        "confidence": 0.95,
        "model": "gpt-4o",
        "tokens": 42,
        "document_analysis": {
            "document_type": "invoice",
            "language": "en",
            "page_count": 2,
            "key_fields": {"total": 10.0},
        },
    }
    with patch(
        "app.api.v1.vision.VisionService.scan_document",
        new=AsyncMock(return_value=payload),
    ):
        resp = await client.post("/api/v1/vision/scan", files={"file": ("doc.png", b"data", "image/png")})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["raw_text"] == "INVOICE #123"
    assert body["structured_data"]["total"] == 10.0
    assert body["confidence"] == 0.95
    assert body["document_analysis"]["document_type"] == "invoice"
    assert body["document_analysis"]["key_fields"]["total"] == 10.0
    # schema serializes through the typed models, not a raw dict
    assert isinstance(ScanDocumentResponse.model_validate(body), ScanDocumentResponse)
    assert isinstance(
        DocumentAnalysisResponse.model_validate(body["document_analysis"]),
        DocumentAnalysisResponse,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vision_scan_empty_and_partial_analysis_defaults(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    for payload in [
        {"raw_text": "", "structured_data": {}, "confidence": 0.0,
         "model": "gpt-4o", "tokens": 0, "document_analysis": {}},
        {"raw_text": "text", "structured_data": {}, "confidence": 0.95,
         "model": "gpt-4o", "tokens": 10, "document_analysis": {"document_type": "unknown"}},
        {"raw_text": "text", "structured_data": {}, "confidence": 0.95,
         "model": "gpt-4o", "tokens": 10,
         "document_analysis": {"document_type": "receipt", "page_count": 1}},
    ]:
        with patch(
            "app.api.v1.vision.VisionService.scan_document",
            new=AsyncMock(return_value=payload),
        ):
            resp = await client.post(
                "/api/v1/vision/scan",
                files={"file": ("doc.png", b"data", "image/png")},
            )
        assert resp.status_code == 200, resp.text
        analysis = resp.json()["document_analysis"]
        assert analysis["document_type"] in ("unknown", "receipt")
        assert analysis["language"] == "unknown"
        assert isinstance(analysis["key_fields"], dict)
        assert analysis["page_count"] in (None, 1)


# ---------------------------------------------------------------------------
# v4 ecosystem builder generate
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ecosystem_generate_response_is_typed(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    app = AIAppDefinition(
        organization_id=user.organization_id,
        user_id=user.id,
        name="Support Bot",
        natural_language_prompt="Build a support bot",
        status="building",
    )
    db.add(app)
    payload = {"app": app, "suggestion": "Suggested architecture: RAG pipeline."}
    with patch(
        "app.services.v4.ecosystem_service.EcosystemService.generate_from_prompt",
        new=AsyncMock(return_value=payload),
    ):
        resp = await client.post(f"{ECOSYSTEM}/builder/apps/{app.id}/generate")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["suggestion"].startswith("Suggested architecture")
    assert body["app"]["name"] == "Support Bot"
    assert body["app"]["status"] == "building"
    # UUID fields serialize as canonical UUID strings
    assert uuid.UUID(body["app"]["id"]) == app.id
    assert isinstance(AIAppGenerateResponse.model_validate(body), AIAppGenerateResponse)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ecosystem_generate_missing_app_404(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    with patch(
        "app.services.v4.ecosystem_service.EcosystemService.generate_from_prompt",
        new=AsyncMock(return_value=None),
    ):
        resp = await client.post(f"{ECOSYSTEM}/builder/apps/{uuid.uuid4()}/generate")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# v6 governance reviews
# ---------------------------------------------------------------------------


async def _create_decision(client, user):
    resp = await client.post(f"{GOVERNANCE}/decisions", json={
        "user_id": "", "organization_id": str(user.organization_id),
        "session_id": "schema-sess", "model": "gpt-4o", "prompt_version": "v1",
        "input_text": "Draft a contract", "output_text": "Liability clause",
        "sources": [], "tools_used": [], "risk_level": "high",
        "requires_review": True, "final_action": "proposed",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_review_create_and_get_typed(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    decision_id = await _create_decision(client, user)

    created = await client.post(f"{GOVERNANCE}/reviews", json={
        "decision_id": decision_id,
        "reviewer_id": str(user.id),
        "risk_level": "high",
        "input_summary": "Draft contract",
        "output_summary": "Contract drafted",
    })
    assert created.status_code == 200, created.text
    body = created.json()
    assert uuid.UUID(body["id"])
    assert body["decision_id"] == decision_id
    assert body["reviewer_id"] == str(user.id)
    assert body["status"] == "pending"
    assert body["risk_level"] == "high"
    assert body["input_summary"] == "Draft contract"
    assert body["output_summary"] == "Contract drafted"
    assert isinstance(ReviewResponse.model_validate(body), ReviewResponse)

    fetched = (await client.get(f"{GOVERNANCE}/reviews/{body['id']}")).json()
    assert fetched["id"] == body["id"]
    assert fetched["decision_id"] == decision_id
    assert fetched["comments"] is None
    assert isinstance(ReviewResponse.model_validate(fetched), ReviewResponse)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_review_approve_reject_typed(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    decision_id = await _create_decision(client, user)

    created = (await client.post(f"{GOVERNANCE}/reviews", json={
        "decision_id": decision_id, "reviewer_id": str(user.id),
        "risk_level": "medium", "input_summary": "x", "output_summary": "y",
    })).json()
    review_id = created["id"]

    approved = await client.post(f"{GOVERNANCE}/reviews/{review_id}/approve", json={"comments": "OK"})
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["status"] == "approved"
    assert uuid.UUID(body["review_id"]) == uuid.UUID(review_id)
    assert isinstance(ReviewActionResponse.model_validate(body), ReviewActionResponse)

    second = (await client.post(f"{GOVERNANCE}/reviews", json={
        "decision_id": "", "reviewer_id": str(user.id),
        "risk_level": "low", "input_summary": "a", "output_summary": "b",
    })).json()
    rejected = await client.post(f"{GOVERNANCE}/reviews/{second['id']}/reject", json={"comments": "No"})
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"

    done = await client.post(f"{GOVERNANCE}/reviews/{review_id}/approve", json={"comments": ""})
    assert done.status_code == 404


# ---------------------------------------------------------------------------
# v6 governance feedback
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_feedback_response_typed(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    decision_id = await _create_decision(client, user)

    resp = await client.post(f"{GOVERNANCE}/feedback", json={
        "decision_id": decision_id, "model": "gpt-4o", "rating": 4,
        "rating_type": "helpful", "correction": "", "comment": "Solid",
        "category": "accuracy",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert uuid.UUID(body["id"])
    assert body["status"] == "received"
    assert body["decision_id"] == decision_id
    assert body["rating"] == 4
    assert body["comment"] == "Solid"
    assert body["category"] == "accuracy"
    assert body["created_at"] is not None
    assert isinstance(FeedbackResponse.model_validate(body), FeedbackResponse)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_feedback_without_optional_comments(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    resp = await client.post(f"{GOVERNANCE}/feedback", json={
        "decision_id": "", "model": "gpt-4o", "rating": 5,
        "rating_type": "thumbs", "correction": "", "comment": "",
        "category": "",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["decision_id"] is None
    assert body["comment"] == ""
    assert isinstance(FeedbackResponse.model_validate(body), FeedbackResponse)


# ---------------------------------------------------------------------------
# v6 governance dashboard
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_governance_dashboard_empty_is_typed(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    dashboard = (await client.get(f"{GOVERNANCE}/dashboard")).json()
    assert dashboard == {
        "prompt_count": 0, "evaluation_count": 0, "review_count": 0,
        "feedback_count": 0, "decision_count": 0, "passed_evaluations": 0,
        "health_score": 0.0,
    }
    assert isinstance(
        GovernanceDashboardResponse.model_validate(dashboard), GovernanceDashboardResponse
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_governance_dashboard_seeded_typed(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    db.add(PromptRegistry(name="P1", category="support", owner="u1",
                          status="draft", current_version=1))
    db.add(AIEvaluation(model="gpt-4o", input_text="i", output_text="o",
                        accuracy_score=90.0, safety_score=90.0, passed=True))
    db.add(HumanReview(decision_id=uuid.uuid4(), reviewer_id=uuid.uuid4(),
                       risk_level="low", status="pending"))
    db.add(UserFeedback(user_id=uuid.uuid4(), model="gpt-4o", rating=3,
                        rating_type="thumbs"))

    dashboard = (await client.get(f"{GOVERNANCE}/dashboard")).json()
    assert dashboard["prompt_count"] == 1
    assert dashboard["evaluation_count"] == 1
    assert dashboard["passed_evaluations"] == 1
    assert dashboard["review_count"] == 1
    assert dashboard["feedback_count"] == 1
    assert dashboard["health_score"] == 100.0
    assert isinstance(
        GovernanceDashboardResponse.model_validate(dashboard), GovernanceDashboardResponse
    )


# ---------------------------------------------------------------------------
# UUID serialization consistency across the typed responses
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_review_uuid_roundtrip_consistency(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    decision_id = await _create_decision(client, user)
    created = (await client.post(f"{GOVERNANCE}/reviews", json={
        "decision_id": decision_id, "reviewer_id": str(user.id),
        "risk_level": "high", "input_summary": "x", "output_summary": "y",
    })).json()

    # the id returned by create must be reusable everywhere: get, approve
    assert created["decision_id"] == decision_id
    fetched = (await client.get(f"{GOVERNANCE}/reviews/{created['id']}")).json()
    assert fetched["id"] == created["id"]
    approved = (await client.post(
        f"{GOVERNANCE}/reviews/{created['id']}/approve", json={"comments": ""}
    )).json()
    assert approved["review_id"] == created["id"]

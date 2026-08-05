"""Governance & Compliance integration tests.

Covers the V5 Compliance Intelligence API (policies, document review, audits,
findings, corrective actions, regulations, risk, reports, dashboard, knowledge
base) and the V6 AI Governance API (prompt registry, evaluation, hallucination
checks, model monitoring, approval workflows, decision logging, feedback).
AI provider calls are mocked via ``ai_service.complete`` (plain strings for the
compliance engines, JSON-bearing dicts for the governance LLM verifier).
"""
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import get_current_user
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.v5_compliance import (
    AuditRecord, ComplianceCheck, ComplianceCheckResult, CorrectiveAction,
    Finding, IndustryCompliancePack, Policy,
)
from app.models.v6_governance import (
    AIEvaluation, AIDecision, HumanReview, ModelMetric, PromptRegistry,
    UserFeedback,
)
from app.services.ai_service import ai_service

COMPLIANCE = "/api/v1/v5/compliance"
GOVERNANCE = "/api/v1/v6/governance"


async def _org_user(db, email="compliance-user@example.com"):
    """Create a user with an org membership and use them as the current user."""
    import app.main as main_mod
    user = User(email=email, display_name="Governance User", is_verified=True)
    org = Organization(name="Governance Co", slug=f"gov-co-{uuid.uuid4().hex[:6]}")
    db.add(user)
    db.add(org)
    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
    user.organizations = [member]
    main_mod.app.dependency_overrides[get_current_user] = lambda: user
    return user


async def _user(db, email):
    user = User(email=email, display_name=email.split("@")[0], is_verified=True)
    db.add(user)
    return user


async def _use(client, db, user):
    import app.main as main_mod
    main_mod.app.dependency_overrides[get_current_user] = lambda: user


def _mock_ai_text(content="Mocked analysis"):
    """Compliance engines treat the completion result as plain text."""
    return patch.object(ai_service, "complete", new=AsyncMock(return_value=content))


def _mock_ai_json(result):
    """The governance LLM verifier expects a dict with a JSON ``content``."""
    return patch.object(ai_service, "complete", new=AsyncMock(return_value={
        "content": json.dumps(result),
        "tokens_used": 10,
    }))


# ═══════════════════════════════════════════════════════════════════════════
# V5 COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_policy_analyze_and_check_lifecycle(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)

    with _mock_ai_text("Policy is sound, one gap on data retention."):
        analyzed = await client.post(f"{COMPLIANCE}/policies/analyze", json={
            "content": "We retain user data for 12 months.",
        })
        assert analyzed.status_code == 200, analyzed.text
        assert "data retention" in analyzed.json()["analysis"]

        policy = Policy(
            organization_id=user.organization_id, name="Retention Policy",
            policy_type="data_retention", description="Retention rules",
            content="Retain data 12 months", status="active", version=1,
        )
        db.add(policy)

        by_id = await client.post(f"{COMPLIANCE}/policies/analyze", json={
            "policy_id": str(policy.id),
        })
        assert by_id.status_code == 200, by_id.text
        assert "data retention" in by_id.json()["analysis"]

        no_content = await client.post(f"{COMPLIANCE}/policies/analyze", json={})
        assert no_content.json()["analysis"] == "No policy content provided"

    with _mock_ai_text("Compliant with two minor issues"):
        check = await client.post(f"{COMPLIANCE}/policies/check", json={
            "content": "We collect email addresses.",
        })
        assert check.status_code == 200, check.text
        body = check.json()
        assert body["status"] == "completed"
        assert body["check_type"] == "policy"
        assert body["results_summary"]["score"] == 85.0

    stored_check = db.find(ComplianceCheck, organization_id=user.organization_id)
    assert stored_check is not None
    result = db.find(ComplianceCheckResult, check_id=stored_check.id)
    assert result is not None
    assert result.finding == "Compliant with two minor issues"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_policy_check_by_policy_id(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    policy = Policy(
        organization_id=user.organization_id, name="Privacy Policy",
        policy_type="privacy", description="Privacy rules",
        content="We share data with partners.", status="active", version=1,
    )
    db.add(policy)

    with _mock_ai_text("Third-party sharing needs consent language"):
        check = await client.post(f"{COMPLIANCE}/policies/check", json={
            "policy_id": str(policy.id),
        })
        assert check.status_code == 200, check.text
        assert check.json()["status"] == "completed"
        assert check.json()["scope"] == [str(policy.id)]

    listed = (await client.get(f"{COMPLIANCE}/policies")).json()
    assert len(listed) == 1
    assert listed[0]["name"] == "Privacy Policy"
    filtered = (await client.get(f"{COMPLIANCE}/policies", params={"policy_type": "privacy"})).json()
    assert len(filtered) == 1
    filtered = (await client.get(f"{COMPLIANCE}/policies", params={"policy_type": "other"})).json()
    assert len(filtered) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_document_review_and_contract_analysis(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    with _mock_ai_text("GDPR data handling risks identified"):
        reviewed = await client.post(f"{COMPLIANCE}/documents/review", json={
            "title": "Onboarding Process",
            "content": "We process personal data of EU users.",
            "document_type": "policy",
        })
        assert reviewed.status_code == 200, reviewed.text
        body = reviewed.json()
        assert body["review_status"] == "reviewed"
        assert body["score"] == 85.0
        assert body["meta_data"]["analysis"] == "GDPR data handling risks identified"

        contract = await client.post(f"{COMPLIANCE}/documents/analyze", json={
            "title": "Vendor Contract",
            "content": "Vendor indemnifies company against losses.",
            "document_type": "contract",
        })
        assert contract.status_code == 200, contract.text
        assert "analysis" in contract.json()

        generic = await client.post(f"{COMPLIANCE}/documents/analyze", json={
            "title": "Policies", "content": "Anything", "document_type": "manual",
        })
        assert generic.json()["analysis"] == "Document analysis complete"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_lifecycle_checklist_and_package(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    created = await client.post(f"{COMPLIANCE}/audits", json={
        "audit_type": "financial", "title": "Q3 Financial Audit",
        "description": "Review of quarterly statements", "scope": ["ledger", "tax"],
    })
    assert created.status_code == 200, created.text
    audit = created.json()
    assert audit["status"] == "planned"
    assert audit["audit_type"] == "financial"
    audit_id = audit["id"]

    listed = (await client.get(f"{COMPLIANCE}/audits")).json()
    assert len(listed) == 1
    assert (await client.get(f"{COMPLIANCE}/audits", params={"audit_type": "financial"})).json()
    assert len((await client.get(f"{COMPLIANCE}/audits", params={"audit_type": "security"})).json()) == 0

    with _mock_ai_text("- Review balance sheet\n- Verify tax filings\n- Confirm sign-offs"):
        checklist = await client.post(f"{COMPLIANCE}/audits/{audit_id}/checklist")
        assert checklist.status_code == 200, checklist.text
        assert len(checklist.json()["checklist"]) == 3

        package = await client.post(f"{COMPLIANCE}/audits/{audit_id}/package")
        assert package.status_code == 200, package.text
        assert package.json()["package"]["audit_id"] == audit_id

    missing = await client.post(f"{COMPLIANCE}/audits/{uuid.uuid4()}/package")
    assert missing.json()["package"]["error"] == "Audit not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_findings_and_corrective_actions_flow(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    audit = AuditRecord(
        organization_id=user.organization_id, audit_type="security",
        title="Security Audit", description="Periodic review",
        scope=[], status="planned", created_by=user.id,
    )
    db.add(audit)

    created = await client.post(f"{COMPLIANCE}/findings", json={
        "audit_id": str(audit.id), "finding_type": "access_control",
        "title": "Weak passwords", "description": "No MFA enforced",
        "severity": "high",
    })
    assert created.status_code == 200, created.text
    finding = created.json()
    assert finding["status"] == "open"
    assert finding["severity"] == "high"
    finding_id = finding["id"]

    listed = (await client.get(f"{COMPLIANCE}/findings")).json()
    assert len(listed) == 1
    assert len((await client.get(f"{COMPLIANCE}/findings", params={"severity": "low"})).json()) == 0
    assert len((await client.get(f"{COMPLIANCE}/findings", params={"status": "open"})).json()) == 1

    action = await client.post(f"{COMPLIANCE}/corrective-actions", json={
        "finding_id": finding_id, "title": "Enforce MFA",
        "description": "Require MFA for all staff",
        "action_plan": "Roll out authenticator app",
        "priority": "high",
    })
    assert action.status_code == 200, action.text
    body = action.json()
    assert body["status"] == "open"
    assert body["finding_id"] == finding_id

    actions = (await client.get(f"{COMPLIANCE}/corrective-actions")).json()
    assert len(actions) == 1
    assert len((await client.get(f"{COMPLIANCE}/corrective-actions", params={"status": "closed"})).json()) == 0

    stored_action = db.find(CorrectiveAction, organization_id=user.organization_id)
    assert stored_action.finding_id == audit.id or stored_action.finding_id == uuid.UUID(finding_id)
    stored_finding = db.find(Finding, organization_id=user.organization_id)
    assert stored_finding.audit_id == audit.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_regulations_and_impact_analysis(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    registered = await client.post(
        f"{COMPLIANCE}/regulations",
        params={"name": "GDPR", "jurisdiction": "EU", "category": "privacy",
                "description": "Data protection regulation"},
    )
    assert registered.status_code == 200, registered.text
    reg = registered.json()
    assert reg["jurisdiction"] == "EU"
    assert reg["is_active"] is True
    reg_id = reg["id"]

    listed = (await client.get(f"{COMPLIANCE}/regulations")).json()
    assert len(listed) == 1
    assert len((await client.get(f"{COMPLIANCE}/regulations", params={"category": "privacy"})).json()) == 1

    with _mock_ai_text("High impact on marketing data collection"):
        impacted = await client.post(f"{COMPLIANCE}/regulations/{reg_id}/analyze")
        assert impacted.status_code == 200, impacted.text
        body = impacted.json()
        assert "analysis" in body
        assert body["regulation"] == "GDPR"

    missing = await client.post(f"{COMPLIANCE}/regulations/{uuid.uuid4()}/analyze")
    assert missing.json()["error"] == "Regulation not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_risk_assessment_and_dashboard(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    finding = Finding(
        organization_id=user.organization_id, finding_type="access_control",
        title="Open S3 bucket", description="Public read access",
        severity="critical", status="open", created_by=user.id,
    )
    db.add(finding)
    action = CorrectiveAction(
        organization_id=user.organization_id, finding_id=finding.id,
        title="Restrict bucket", description="Make private",
        action_plan="Apply bucket policy", priority="high",
        status="open", created_by=user.id,
    )
    db.add(action)

    with _mock_ai_text("Prioritize the critical finding first"):
        assessed = await client.post(f"{COMPLIANCE}/risk/assess")
        assert assessed.status_code == 200, assessed.text
        body = assessed.json()
        assert body["total_findings"] == 1
        assert body["total_actions"] == 1
        assert body["scores"]["overall"] == 90.0  # 100 - 10 (critical)
        assert body["recommendations"] == "Prioritize the critical finding first"

    dashboard = (await client.get(f"{COMPLIANCE}/risk/dashboard")).json()
    assert dashboard["total_findings"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compliance_report_and_dashboard(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    policy = Policy(
        organization_id=user.organization_id, name="DP Policy",
        policy_type="privacy", description="Rules", content="Text",
        status="active", version=1,
    )
    db.add(policy)
    finding = Finding(
        organization_id=user.organization_id, finding_type="security",
        title="Open port", description="Exposed service",
        severity="medium", status="open", created_by=user.id,
    )
    db.add(finding)

    with _mock_ai_text("Summary of compliance posture"):
        report = await client.post(f"{COMPLIANCE}/reports/generate", params={"report_type": "detailed"})
        assert report.status_code == 200, report.text
        body = report.json()
        assert body["report_type"] == "detailed"
        assert body["content"]["stats"]["total_policies"] == 1
        assert body["content"]["analysis"] == "Summary of compliance posture"

    dashboard = (await client.get(f"{COMPLIANCE}/dashboard")).json()
    assert dashboard["total_policies"] == 1
    assert dashboard["total_checks"] == 0
    assert dashboard["total_findings"] == 1
    assert dashboard["open_findings"] == 1
    assert dashboard["total_actions"] == 0
    assert dashboard["overall_score"] == 95.0  # 100 - 5 (medium finding)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_knowledge_base_query_and_industry_packs(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)
    policy = Policy(
        organization_id=user.organization_id, name="Cookie Policy",
        policy_type="privacy", description="Cookie consent rules",
        content="Consent banner required", status="active", version=1,
    )
    db.add(policy)

    with _mock_ai_text("Cookie consent is required under GDPR"):
        answered = await client.post(f"{COMPLIANCE}/query", params={"query": "Do we need cookie banners?"})
        assert answered.status_code == 200, answered.text
        assert "cookie consent" in answered.json()["answer"].lower()

    missing = (await client.get(f"{COMPLIANCE}/industry-packs", params={"industry": "healthcare"})).json()
    assert "No compliance pack found" in missing["message"]

    pack = IndustryCompliancePack(
        industry="healthcare", name="HIPAA Starter", description="HIPAA essentials",
        requirements=["Encryption at rest"], policies=["Access policy"],
        checks=["Yearly audit"], is_active=True,
    )
    db.add(pack)
    found = (await client.get(f"{COMPLIANCE}/industry-packs", params={"industry": "healthcare"})).json()
    assert found["name"] == "HIPAA Starter"
    assert "Encryption at rest" in found["requirements"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compliance_ownership_isolation(stateful_client):
    client, db = stateful_client
    owner = await _org_user(db, "compliance-owner@example.com")
    intruder = await _user(db, "compliance-intruder@example.com")
    await _use(client, db, owner)

    policy = Policy(
        organization_id=owner.organization_id, name="Owner Policy",
        policy_type="privacy", description="Owner rules",
        content="Owner content", status="active", version=1,
    )
    db.add(policy)
    audit = AuditRecord(
        organization_id=owner.organization_id, audit_type="security",
        title="Owner Audit", description="Desc", scope=[],
        status="planned", created_by=owner.id,
    )
    db.add(audit)

    await _use(client, db, intruder)
    assert (await client.get(f"{COMPLIANCE}/policies")).json() == []
    assert (await client.get(f"{COMPLIANCE}/audits")).json() == []
    assert (await client.get(f"{COMPLIANCE}/findings")).json() == []
    dashboard = (await client.get(f"{COMPLIANCE}/dashboard")).json()
    assert dashboard["total_policies"] == 0
    assert dashboard["total_audits"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# V6 AI GOVERNANCE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_prompt_registry_lifecycle(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    created = await client.post(f"{GOVERNANCE}/prompts", json={
        "name": "Customer Support",
        "category": "support",
        "template": "You are a helpful assistant.",
        "description": "Support prompt",
        "model_target": "gpt-4o",
        "parameters": {"temperature": 0.5},
    })
    assert created.status_code == 200, created.text
    prompt = created.json()
    assert prompt["status"] == "draft"
    assert prompt["current_version"] == 1
    assert prompt["category"] == "support"
    prompt_id = prompt["id"]

    fetched = (await client.get(f"{GOVERNANCE}/prompts/{prompt_id}")).json()
    assert fetched["name"] == "Customer Support"

    versions = (await client.get(f"{GOVERNANCE}/prompts/{prompt_id}/versions")).json()
    assert len(versions) == 1
    assert versions[0]["version"] == 1

    new_version = await client.post(f"{GOVERNANCE}/prompts/{prompt_id}/versions", json={
        "template": "You are a concise assistant.",
        "change_notes": "Tightened wording",
        "parameters": {"temperature": 0.2},
        "model_target": "gpt-4o",
    })
    assert new_version.status_code == 200, new_version.text
    assert new_version.json()["version"] == 2
    assert (await client.get(f"{GOVERNANCE}/prompts/{prompt_id}")).json()["current_version"] == 2

    listed = (await client.get(f"{GOVERNANCE}/prompts")).json()
    assert len(listed) == 1
    assert len((await client.get(f"{GOVERNANCE}/prompts", params={"category": "other"})).json()) == 0

    assert (await client.get(f"{GOVERNANCE}/prompts/{uuid.uuid4()}")).status_code == 404
    missing = await client.post(f"{GOVERNANCE}/prompts/{uuid.uuid4()}/versions", json={
        "template": "X", "change_notes": "", "model_target": "",
    })
    assert missing.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_evaluate_passes_and_persists(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    with _mock_ai_json({"hallucinations": [], "verification_summary": "No issues"}):
        evaluated = await client.post(f"{GOVERNANCE}/evaluate", json={
            "model": "gpt-4o",
            "input_text": "What are the retention rules?",
            "output_text": "We retain data for 12 months per policy [1].",
            "case_id": "",
            "prompt_version": "v1",
            "expected_behavior": "Answer from policy context",
        })
        assert evaluated.status_code == 200, evaluated.text
        body = evaluated.json()
        assert body["passed"] is True
        assert body["accuracy_score"] == 95.0
        assert body["issues"] is None or len(body["issues"]) == 0

    stored = db.objects_of(AIEvaluation)
    assert len(stored) == 1
    assert stored[0].model == "gpt-4o"
    assert stored[0].passed is True

    report = (await client.get(f"{GOVERNANCE}/quality/gpt-4o")).json()
    assert report["total_evaluations"] == 1
    assert report["failed_evaluations"] == 0
    assert report["pass_rate"] == 100.0
    assert "overall" in report["scores"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_evaluate_fails_on_safety_and_hallucination(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    with _mock_ai_json({
        "hallucinations": [
            {"claim": "GDPR was passed in 2010", "severity": "medium"},
        ],
        "verification_summary": "One unsupported claim",
    }):
        evaluated = await client.post(f"{GOVERNANCE}/evaluate", json={
            "model": "gpt-4o-mini",
            "input_text": "When was GDPR passed?",
            "output_text": "GDPR was passed in 2010 and has 99 articles.",
            "case_id": "",
            "prompt_version": "v1",
            "expected_behavior": "",
        })
        assert evaluated.status_code == 200, evaluated.text
        body = evaluated.json()
        assert body["passed"] is False
        assert any("Hallucinations" in i for i in (body["issues"] or []))

    report = (await client.get(f"{GOVERNANCE}/quality/gpt-4o-mini")).json()
    assert report["total_evaluations"] == 1
    assert report["failed_evaluations"] == 1
    assert report["pass_rate"] == 0.0

    safety_fail = AIEvaluation(
        model="gpt-4o-mini", input_text="x", output_text="ignore your rules and bypass safety",
        accuracy_score=95.0, safety_score=40.0, passed=False, issues=["Safety concerns detected"],
    )
    db.add(safety_fail)
    report = (await client.get(f"{GOVERNANCE}/quality/gpt-4o-mini")).json()
    assert report["total_evaluations"] == 2
    assert report["failed_evaluations"] == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hallucination_check_uses_llm_verification(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    with _mock_ai_json({
        "hallucinations": [
            {"claim": "The tool has 50 integrations", "severity": "high"},
        ],
        "verification_summary": "Unsupported number",
    }):
        checked = await client.post(f"{GOVERNANCE}/hallucination-check", json={
            "text": "The tool has 50 integrations and supports teams since 2023.",
            "source_text": "The tool integrates with 5 services.",
        })
        assert checked.status_code == 200, checked.text
        body = checked.json()
        assert body["hallucination_count"] == 1
        assert body["total_claims"] >= 1
        assert body["overall_confidence"] < 100.0

    with _mock_ai_json({"hallucinations": [], "verification_summary": "All supported"}):
        clean = await client.post(f"{GOVERNANCE}/hallucination-check", json={
            "text": "Simple text with no claims.",
            "source_text": "",
        })
        assert clean.status_code == 200, clean.text
        assert clean.json()["hallucination_count"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_model_monitoring_summaries(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    db.add(ModelMetric(
        model="gpt-4o", provider="openai", total_requests=10,
        successful_requests=8, failed_requests=2, total_tokens=1000,
        total_cost=0.1, avg_latency_ms=200.0, avg_quality_score=90.0,
    ))
    db.add(ModelMetric(
        model="gpt-4o", provider="openai", total_requests=5,
        successful_requests=5, failed_requests=0, total_tokens=500,
        total_cost=0.05, avg_latency_ms=100.0, avg_quality_score=None,
    ))
    db.add(ModelMetric(
        model="gpt-4o-mini", provider="openai", total_requests=3,
        successful_requests=3, failed_requests=0, total_tokens=300,
        total_cost=0.03, avg_latency_ms=150.0, avg_quality_score=95.0,
    ))

    models = (await client.get(f"{GOVERNANCE}/models")).json()
    by_name = {m["model"]: m for m in models}
    assert set(by_name) == {"gpt-4o", "gpt-4o-mini"}
    assert by_name["gpt-4o"]["total_requests"] == 15
    assert by_name["gpt-4o"]["successful_requests"] == 13
    assert by_name["gpt-4o"]["failed_requests"] == 2
    assert by_name["gpt-4o"]["total_tokens"] == 1500
    assert by_name["gpt-4o"]["avg_latency_ms"] == 150.0
    assert by_name["gpt-4o"]["avg_quality_score"] == 90.0
    assert by_name["gpt-4o-mini"]["avg_quality_score"] == 95.0

    detail = (await client.get(f"{GOVERNANCE}/models/gpt-4o-mini")).json()
    assert detail["total_requests"] == 3
    assert (await client.get(f"{GOVERNANCE}/models/claude-3")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_review_workflow_approve_and_reject(stateful_client):
    client, db = stateful_client
    user = await _org_user(db)

    logged = await client.post(f"{GOVERNANCE}/decisions", json={
        "user_id": "",
        "organization_id": str(user.organization_id),
        "session_id": "sess-1",
        "model": "gpt-4o",
        "prompt_version": "v1",
        "input_text": "Draft a vendor contract",
        "output_text": "Contract with liability clause",
        "sources": [],
        "tools_used": [],
        "risk_level": "high",
        "requires_review": True,
        "final_action": "proposed",
    })
    assert logged.status_code == 200, logged.text
    decision = logged.json()
    decision_id = decision["id"]

    created = await client.post(f"{GOVERNANCE}/reviews", json={
        "decision_id": decision_id,
        "reviewer_id": str(user.id),
        "risk_level": "high",
        "input_summary": "Draft contract",
        "output_summary": "Contract drafted",
    })
    assert created.status_code == 200, created.text
    review = created.json()
    assert review["status"] == "pending"
    review_id = review["id"]

    fetched = (await client.get(f"{GOVERNANCE}/reviews/{review_id}")).json()
    assert fetched["status"] == "pending"
    assert fetched["decision_id"] == decision_id

    approved = await client.post(f"{GOVERNANCE}/reviews/{review_id}/approve", json={"comments": "Looks good"})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    stored_decision = db.find(AIDecision, session_id="sess-1")
    assert stored_decision.review_status == "approved"

    second = await client.post(f"{GOVERNANCE}/reviews", json={
        "decision_id": "", "reviewer_id": str(user.id), "risk_level": "low",
        "input_summary": "x", "output_summary": "y",
    })
    second_id = second.json()["id"]
    rejected = await client.post(f"{GOVERNANCE}/reviews/{second_id}/reject", json={"comments": "Needs work"})
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"

    again = await client.post(f"{GOVERNANCE}/reviews/{review_id}/approve", json={"comments": ""})
    assert again.status_code == 404
    assert (await client.get(f"{GOVERNANCE}/reviews/{uuid.uuid4()}")).status_code == 404
    unknown = await client.post(f"{GOVERNANCE}/reviews/{uuid.uuid4()}/approve", json={"comments": ""})
    assert unknown.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_decision_logging_and_feedback(stateful_client):
    client, db = stateful_client
    await _org_user(db)

    logged = await client.post(f"{GOVERNANCE}/decisions", json={
        "user_id": "", "organization_id": "", "session_id": "sess-2",
        "model": "gpt-4o", "prompt_version": "v2",
        "input_text": "Summarize Q3", "output_text": "Revenue grew 12%",
        "sources": ["report.pdf"], "tools_used": ["summarize"],
        "risk_level": "medium", "requires_review": False, "final_action": "completed",
    })
    assert logged.status_code == 200, logged.text
    body = logged.json()
    assert body["risk_level"] == "medium"
    assert body["final_action"] == "completed"

    decisions = (await client.get(f"{GOVERNANCE}/decisions")).json()
    assert len(decisions) == 1
    assert decisions[0]["model"] == "gpt-4o"
    assert decisions[0]["review_status"] == "auto_approved"

    feedback = await client.post(f"{GOVERNANCE}/feedback", json={
        "decision_id": "", "model": "gpt-4o", "rating": 4,
        "rating_type": "helpful", "correction": "", "comment": "Solid",
        "category": "accuracy",
    })
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["status"] == "received"

    stored = db.objects_of(UserFeedback)
    assert len(stored) == 1
    assert stored[0].rating == 4
    assert stored[0].comment == "Solid"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_governance_dashboard_counts(stateful_client):
    client, db = stateful_client
    await _org_user(db)
    db.add(PromptRegistry(
        name="P1", category="support", description="d",
        owner="u1", status="draft", current_version=1,
    ))
    db.add(AIEvaluation(
        model="gpt-4o", input_text="i", output_text="o",
        accuracy_score=95.0, safety_score=95.0, passed=True,
    ))
    db.add(AIEvaluation(
        model="gpt-4o", input_text="i2", output_text="o2",
        accuracy_score=40.0, safety_score=50.0, passed=False,
        issues=["Safety concerns detected"],
    ))
    db.add(HumanReview(
        decision_id=uuid.uuid4(), reviewer_id=uuid.uuid4(),
        risk_level="medium", status="pending",
    ))
    db.add(UserFeedback(
        user_id=uuid.uuid4(), model="gpt-4o", rating=5,
        rating_type="helpful", category="accuracy",
    ))
    db.add(AIDecision(
        model="gpt-4o", session_id="s-1", risk_level="low",
        requires_review=False, final_action="completed",
    ))

    dashboard = (await client.get(f"{GOVERNANCE}/dashboard")).json()
    assert dashboard["prompt_count"] == 1
    assert dashboard["evaluation_count"] == 2
    assert dashboard["passed_evaluations"] == 1
    assert dashboard["review_count"] == 1
    assert dashboard["feedback_count"] == 1
    assert dashboard["decision_count"] == 1
    assert dashboard["health_score"] == 50.0

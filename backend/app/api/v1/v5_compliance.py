import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v5_compliance import (
    AnalyzeDocumentRequest,
    AuditRecordResponse,
    CheckPolicyRequest,
    ComplianceCheckResponse,
    ComplianceDocumentReviewResponse,
    ComplianceReportResponse,
    CorrectiveActionResponse,
    CreateAuditRequest,
    CreateCorrectiveActionRequest,
    CreateFindingRequest,
    FindingResponse,
    PolicyResponse,
    RegulationResponse,
    ReviewDocumentRequest,
)
from app.services.compliance_engine.audit_assistant import AuditAssistant
from app.services.compliance_engine.compliance_dashboard_service import ComplianceDashboardService
from app.services.compliance_engine.compliance_knowledge_base import ComplianceKnowledgeBase
from app.services.compliance_engine.compliance_reporting import ComplianceReporting
from app.services.compliance_engine.corrective_action_service import CorrectiveActionService
from app.services.compliance_engine.document_reviewer import DocumentReviewer
from app.services.compliance_engine.policy_manager import PolicyManager
from app.services.compliance_engine.regulation_monitor import RegulationMonitor
from app.services.compliance_engine.risk_engine import RiskEngine

router = APIRouter()


@router.post("/policies/analyze")
async def analyze_policy(req: CheckPolicyRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = PolicyManager(db)
    return await mgr.analyze_policy(req.policy_id, req.content)


@router.post("/policies/check", response_model=ComplianceCheckResponse)
async def check_policy(req: CheckPolicyRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = PolicyManager(db)
    return await mgr.check_policy(current_user.organization_id or current_user.id, req.policy_id, req.content)


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(policy_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_compliance import Policy
    q = select(Policy).where(Policy.organization_id == (current_user.organization_id or current_user.id))
    if policy_type:
        q = q.where(Policy.policy_type == policy_type)
    q = q.order_by(Policy.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.post("/documents/review", response_model=ComplianceDocumentReviewResponse)
async def review_document(req: ReviewDocumentRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    reviewer = DocumentReviewer(db)
    result = await reviewer.review_document(current_user.organization_id or current_user.id, req.title, req.content, req.document_type)
    return result


@router.post("/documents/analyze")
async def analyze_document(req: AnalyzeDocumentRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    reviewer = DocumentReviewer(db)
    return await reviewer.check_contract(req.content) if req.document_type == "contract" else {"analysis": "Document analysis complete"}


@router.post("/audits", response_model=AuditRecordResponse)
async def create_audit(req: CreateAuditRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    assistant = AuditAssistant(db)
    return await assistant.create_audit(current_user.organization_id or current_user.id, req.audit_type, req.title, req.description, req.scope, current_user.id)


@router.get("/audits", response_model=list[AuditRecordResponse])
async def list_audits(audit_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_compliance import AuditRecord
    q = select(AuditRecord).where(AuditRecord.organization_id == (current_user.organization_id or current_user.id))
    if audit_type:
        q = q.where(AuditRecord.audit_type == audit_type)
    q = q.order_by(AuditRecord.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.post("/audits/{audit_id}/checklist")
async def generate_audit_checklist(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    assistant = AuditAssistant(db)
    result = await assistant.prepare_checklist(audit_id)
    return {"checklist": result}


@router.post("/audits/{audit_id}/package")
async def generate_audit_package(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    assistant = AuditAssistant(db)
    result = await assistant.generate_audit_package(audit_id)
    return {"package": result}


@router.post("/findings", response_model=FindingResponse)
async def create_finding(req: CreateFindingRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.v5_compliance import Finding
    f = Finding(organization_id=current_user.organization_id or current_user.id, audit_id=req.audit_id, finding_type=req.finding_type, title=req.title, description=req.description, severity=req.severity, status="open", created_by=current_user.id)
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


@router.get("/findings", response_model=list[FindingResponse])
async def list_findings(severity: str | None = None, status: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_compliance import Finding
    q = select(Finding).where(Finding.organization_id == (current_user.organization_id or current_user.id))
    if severity:
        q = q.where(Finding.severity == severity)
    if status:
        q = q.where(Finding.status == status)
    q = q.order_by(Finding.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.post("/corrective-actions", response_model=CorrectiveActionResponse)
async def create_corrective_action(req: CreateCorrectiveActionRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CorrectiveActionService(db)
    from datetime import datetime
    deadline = datetime.fromisoformat(req.deadline) if req.deadline else None
    return await svc.create_action(current_user.organization_id or current_user.id, req.finding_id, req.title, req.description, req.action_plan, req.priority, req.assigned_to, deadline, current_user.id)


@router.get("/corrective-actions", response_model=list[CorrectiveActionResponse])
async def list_corrective_actions(status: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_compliance import CorrectiveAction
    q = select(CorrectiveAction).where(CorrectiveAction.organization_id == (current_user.organization_id or current_user.id))
    if status:
        q = q.where(CorrectiveAction.status == status)
    q = q.order_by(CorrectiveAction.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.patch("/corrective-actions/{action_id}/status")
async def update_action_status(action_id: uuid.UUID, status: str, verification_notes: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CorrectiveActionService(db)
    result = await svc.update_status(action_id, status, verification_notes)
    return {"status": result.status if result else "not_found"}


@router.post("/regulations", response_model=RegulationResponse)
async def register_regulation(name: str, jurisdiction: str, category: str, description: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    monitor = RegulationMonitor(db)
    return await monitor.register_regulation(current_user.organization_id or current_user.id, name, jurisdiction, category, description)


@router.get("/regulations", response_model=list[RegulationResponse])
async def list_regulations(category: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_compliance import Regulation
    q = select(Regulation).where(Regulation.organization_id == (current_user.organization_id or current_user.id))
    if category:
        q = q.where(Regulation.category == category)
    q = q.order_by(Regulation.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.post("/regulations/{regulation_id}/analyze")
async def analyze_regulation_impact(regulation_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    monitor = RegulationMonitor(db)
    return await monitor.analyze_impact(regulation_id)


@router.post("/risk/assess")
async def assess_risks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = RiskEngine(db)
    return await engine.assess_risks(current_user.organization_id or current_user.id)


@router.get("/risk/dashboard")
async def get_risk_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = RiskEngine(db)
    return await engine.get_risk_dashboard(current_user.organization_id or current_user.id)


@router.post("/reports/generate", response_model=ComplianceReportResponse)
async def generate_compliance_report(report_type: str = "summary", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ComplianceReporting(db)
    return await svc.generate_report(current_user.organization_id or current_user.id, report_type)


@router.get("/dashboard")
async def compliance_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ComplianceDashboardService(db)
    return await svc.get_dashboard(current_user.organization_id or current_user.id)


@router.post("/query")
async def query_compliance(query: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    kb = ComplianceKnowledgeBase(db)
    result = await kb.query(current_user.organization_id or current_user.id, query)
    return {"answer": result}


@router.get("/industry-packs")
async def get_industry_packs(industry: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    kb = ComplianceKnowledgeBase(db)
    return await kb.get_industry_pack(industry)

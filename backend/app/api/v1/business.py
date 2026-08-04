import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.business import (
    ApprovalRequest, BusinessAlert, BusinessMetric, BusinessReport,
    BusinessWorkflow, BusinessWorkflowExecution, FinancialRecord,
    KnowledgeDocument,
)
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.schemas.business import (
    AgentQueryRequest, AgentQueryResponse,
    ApprovalRequestCreate, ApprovalRequestResponse,
    BusinessMetricResponse, BusinessReportResponse,
    FinancialRecordCreate, FinancialRecordResponse,
    KnowledgeDocumentCreate, KnowledgeDocumentResponse,
    WorkflowCreateRequest, WorkflowExecutionResponse, WorkflowResponse,
)
from app.schemas.common import MessageResponse
from app.services.business_agent_service import (
    ApprovalService, BusinessAgentService, BusinessWorkflowService,
    FinancialAnalysisService, KnowledgeService,
)

router = APIRouter()


async def _get_org(org_id: uuid.UUID, db: AsyncSession) -> Organization:
    org = await db.get(Organization, org_id)
    if not org:
        raise NotFoundError("Organization", str(org_id))
    return org


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(
    body: AgentQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _get_org(body.organization_id, db)
    svc = BusinessAgentService(db)
    result = await svc.process_query(
        agent_type=body.agent_type,
        query=body.query,
        organization_id=body.organization_id,
        user_id=current_user.id,
        context=body.context,
    )
    return result


@router.post("/reports/generate", response_model=BusinessReportResponse)
async def generate_report(
    agent_type: str = Query(...),
    report_type: str = Query(...),
    organization_id: uuid.UUID = Query(...),
    period_start: str | None = Query(None),
    period_end: str | None = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    await _get_org(organization_id, db)
    svc = BusinessAgentService(db)
    report = await svc.generate_report(
        agent_type=agent_type,
        report_type=report_type,
        organization_id=organization_id,
        user_id=current_user.id,
        period_start=period_start,
        period_end=period_end,
    )
    return report


@router.get("/reports", response_model=list[BusinessReportResponse])
async def list_reports(
    organization_id: uuid.UUID = Query(...),
    agent_type: str | None = Query(None),
    report_type: str | None = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(BusinessReport).where(BusinessReport.organization_id == organization_id)
    if agent_type:
        query = query.where(BusinessReport.agent_type == agent_type)
    if report_type:
        query = query.where(BusinessReport.report_type == report_type)
    query = query.order_by(BusinessReport.created_at.desc()).limit(50)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/metrics", response_model=list[BusinessMetricResponse])
async def list_metrics(
    organization_id: uuid.UUID = Query(...),
    agent_type: str | None = Query(None),
    metric_key: str | None = Query(None),
    days: int = Query(30),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    from datetime import timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(BusinessMetric).where(
        and_(
            BusinessMetric.organization_id == organization_id,
            BusinessMetric.created_at >= cutoff,
        )
    )
    if agent_type:
        query = query.where(BusinessMetric.agent_type == agent_type)
    if metric_key:
        query = query.where(BusinessMetric.metric_key == metric_key)
    query = query.order_by(BusinessMetric.created_at.desc()).limit(100)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/metrics", response_model=BusinessMetricResponse)
async def create_metric(
    organization_id: uuid.UUID = Query(...),
    agent_type: str = Query(...),
    metric_key: str = Query(...),
    metric_name: str = Query(...),
    value: float = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    metric = BusinessMetric(
        organization_id=organization_id,
        agent_type=agent_type,
        metric_key=metric_key,
        metric_name=metric_name,
        value=value,
    )
    db.add(metric)
    await db.flush()
    return metric


@router.get("/dashboard/{organization_id}")
async def business_dashboard(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    await _get_org(organization_id, db)

    reports = await db.execute(
        select(BusinessReport).where(BusinessReport.organization_id == organization_id)
        .order_by(BusinessReport.created_at.desc()).limit(5)
    )
    alerts = await db.execute(
        select(BusinessAlert).where(
            and_(
                BusinessAlert.organization_id == organization_id,
                BusinessAlert.is_resolved == False,
            )
        ).order_by(BusinessAlert.created_at.desc()).limit(10)
    )
    approvals = await db.execute(
        select(ApprovalRequest).where(
            and_(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.status == "pending",
            )
        ).order_by(ApprovalRequest.created_at.desc()).limit(10)
    )

    metric_summary = await db.execute(
        select(
            BusinessMetric.agent_type,
            func.count(BusinessMetric.id),
            func.avg(BusinessMetric.value),
        ).where(BusinessMetric.organization_id == organization_id)
        .group_by(BusinessMetric.agent_type)
    )

    return {
        "reports": [{"id": str(r.id), "title": r.title, "type": r.report_type, "summary": r.summary, "created": str(r.created_at)} for r in reports.scalars().all()],
        "alerts": [{"id": str(a.id), "title": a.title, "severity": a.severity, "type": a.alert_type} for a in alerts.scalars().all()],
        "pending_approvals": [{"id": str(a.id), "title": a.title, "type": a.request_type, "priority": a.priority} for a in approvals.scalars().all()],
        "metrics_by_agent": {row[0]: {"count": row[1], "avg_value": float(row[2])} for row in metric_summary.all()},
    }


@router.post("/approvals", response_model=ApprovalRequestResponse)
async def create_approval(
    body: ApprovalRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ApprovalService(db)
    req = await svc.create_request(
        org_id=body.organization_id,
        requester_id=current_user.id,
        request_type=body.request_type,
        title=body.title,
        description=body.description,
        priority=body.priority,
        payload=body.payload,
    )
    return req


@router.get("/approvals/pending", response_model=list[ApprovalRequestResponse])
async def list_pending_approvals(
    organization_id: uuid.UUID = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = ApprovalService(db)
    return await svc.list_pending(organization_id)


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    approval_id: uuid.UUID,
    notes: str | None = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = ApprovalService(db)
    return await svc.approve(approval_id, current_user.id, notes)


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    approval_id: uuid.UUID,
    reason: str = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = ApprovalService(db)
    return await svc.reject(approval_id, current_user.id, reason)


@router.post("/financial/records", response_model=FinancialRecordResponse)
async def record_transaction(
    body: FinancialRecordCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = FinancialAnalysisService(db)
    record = await svc.record_transaction(
        org_id=body.organization_id,
        record_type=body.record_type,
        category=body.category,
        amount=body.amount,
        description=body.description,
        currency=body.currency,
        transaction_date=body.transaction_date,
        reference=body.reference,
        donor=body.donor,
        grant_code=body.grant_code,
        budget_line=body.budget_line,
    )
    return record


@router.get("/financial/summary/{organization_id}")
async def financial_summary(
    organization_id: uuid.UUID,
    months: int = Query(12),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = FinancialAnalysisService(db)
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    import dateutil.relativedelta
    start = start - dateutil.relativedelta.relativedelta(months=months)
    return await svc.get_budget_summary(organization_id, start, now)


@router.post("/financial/forecast/{organization_id}")
async def financial_forecast(
    organization_id: uuid.UUID,
    months: int = Query(12),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = FinancialAnalysisService(db)
    return await svc.forecast_budget(organization_id, months)


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    body: WorkflowCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = BusinessWorkflowService(db)
    wf = await svc.create_workflow(
        org_id=body.organization_id,
        name=body.name,
        workflow_type=body.workflow_type,
        trigger=body.trigger,
        steps=body.steps,
    )
    return wf


@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    organization_id: uuid.UUID = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(BusinessWorkflow).where(BusinessWorkflow.organization_id == organization_id)
        .order_by(BusinessWorkflow.created_at.desc())
    )
    return result.scalars().all()


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = BusinessWorkflowService(db)
    execution = await svc.execute_workflow(workflow_id, organization_id)
    return execution


@router.post("/knowledge", response_model=KnowledgeDocumentResponse)
async def add_knowledge(
    body: KnowledgeDocumentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = KnowledgeService(db)
    doc = await svc.add_document(
        org_id=body.organization_id,
        title=body.title,
        content=body.content,
        doc_type=body.doc_type,
        source=body.source,
        tags=body.tags,
    )
    return doc


@router.get("/knowledge/query")
async def query_knowledge(
    organization_id: uuid.UUID = Query(...),
    query: str = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = KnowledgeService(db)
    return await svc.query(organization_id, query)


@router.get("/knowledge", response_model=list[KnowledgeDocumentResponse])
async def list_knowledge(
    organization_id: uuid.UUID = Query(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(KnowledgeDocument).where(
            and_(
                KnowledgeDocument.organization_id == organization_id,
                KnowledgeDocument.is_active == True,
            )
        ).order_by(KnowledgeDocument.created_at.desc()).limit(100)
    )
    return result.scalars().all()


@router.delete("/knowledge/{doc_id}", response_model=MessageResponse)
async def delete_knowledge(
    doc_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = KnowledgeService(db)
    await svc.delete_document(doc_id)
    return MessageResponse(message="Document deleted")


@router.get("/alerts", response_model=list[dict])
async def list_alerts(
    organization_id: uuid.UUID = Query(...),
    unresolved_only: bool = Query(True),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(BusinessAlert).where(BusinessAlert.organization_id == organization_id)
    if unresolved_only:
        query = query.where(BusinessAlert.is_resolved == False)
    query = query.order_by(BusinessAlert.created_at.desc()).limit(50)
    result = await db.execute(query)
    return [{
        "id": str(a.id), "agent_type": a.agent_type, "alert_type": a.alert_type,
        "severity": a.severity, "title": a.title, "message": a.message,
        "is_resolved": a.is_resolved, "created_at": str(a.created_at),
    } for a in result.scalars().all()]

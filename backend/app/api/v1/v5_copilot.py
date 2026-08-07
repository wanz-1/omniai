import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v5_copilot import (
    ApprovalDecision,
    ApprovalRequest,
    CopilotApprovalResponse,
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotConfigResponse,
    CopilotRecommendationResponse,
    CopilotSessionResponse,
    CopilotWorkflowExecutionResponse,
    CopilotWorkflowResponse,
    ExecuteWorkflowRequest,
)
from app.services.industry_copilot.agriculture_copilot import AgricultureCopilot
from app.services.industry_copilot.approval_service import ApprovalService
from app.services.industry_copilot.business_copilot import BusinessCopilot
from app.services.industry_copilot.copilot_analytics_service import CopilotAnalyticsService
from app.services.industry_copilot.copilot_engine import CopilotEngine
from app.services.industry_copilot.education_copilot import EducationCopilot
from app.services.industry_copilot.finance_copilot import FinanceCopilot
from app.services.industry_copilot.hospitality_copilot import HospitalityCopilot
from app.services.industry_copilot.ngo_copilot import NGOCopilot
from app.services.industry_copilot.recommendation_engine import RecommendationEngine

router = APIRouter()


@router.post("/chat", response_model=CopilotChatResponse)
async def chat_with_copilot(req: CopilotChatRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = CopilotEngine(db)
    org_id = current_user.organization_id or current_user.id
    result = await engine.chat(org_id, current_user.id, req.copilot_id, req.message, req.session_id, req.context)
    return CopilotChatResponse(session_id=result["session_id"], reply=result["reply"])


@router.get("/configs", response_model=list[CopilotConfigResponse])
async def list_copilot_configs(industry: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_copilot import CopilotConfig
    q = select(CopilotConfig).where(CopilotConfig.organization_id == (current_user.organization_id or current_user.id))
    if industry:
        q = q.where(CopilotConfig.industry == industry)
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.post("/configs", response_model=CopilotConfigResponse)
async def create_copilot_config(industry: str, name: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = CopilotEngine(db)
    return await engine.get_or_create_config(current_user.organization_id or current_user.id, industry, name, current_user.id)


@router.get("/sessions", response_model=list[CopilotSessionResponse])
async def list_sessions(copilot_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_copilot import CopilotSession
    q = select(CopilotSession).where(CopilotSession.organization_id == (current_user.organization_id or current_user.id))
    if copilot_id:
        q = q.where(CopilotSession.copilot_id == copilot_id)
    q = q.order_by(CopilotSession.updated_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.get("/sessions/{session_id}/messages", response_model=list)
async def get_session_messages(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_copilot import CopilotMessage
    rows = await db.execute(select(CopilotMessage).where(CopilotMessage.session_id == session_id).order_by(CopilotMessage.created_at))
    return [{"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None} for m in rows.scalars().all()]


@router.post("/industry/ngo/analyze-grant")
async def ngo_analyze_grant(grant_description: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = NGOCopilot(db)
    result = await svc.analyze_grant(grant_description)
    return {"result": result}


@router.post("/industry/ngo/draft-proposal")
async def ngo_draft_proposal(org_info: str, grant_info: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = NGOCopilot(db)
    result = await svc.draft_proposal(org_info, grant_info)
    return {"result": result}


@router.post("/industry/ngo/generate-report")
async def ngo_generate_report(report_type: str, data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = NGOCopilot(db)
    result = await svc.generate_report(report_type, data)
    return {"result": result}


@router.post("/industry/finance/analyze-budget")
async def finance_analyze_budget(budget_data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FinanceCopilot(db)
    result = await svc.analyze_budget(budget_data)
    return {"result": result}


@router.post("/industry/finance/forecast")
async def finance_forecast(historical_data: str, period: str = "quarterly", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FinanceCopilot(db)
    result = await svc.forecast(historical_data, period)
    return {"result": result}


@router.post("/industry/finance/detect-anomalies")
async def finance_detect_anomalies(transactions: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FinanceCopilot(db)
    result = await svc.detect_anomalies(transactions)
    return {"result": result}


@router.post("/industry/hospitality/analyze-occupancy")
async def hospitality_analyze_occupancy(occupancy_data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = HospitalityCopilot(db)
    result = await svc.analyze_occupancy(occupancy_data)
    return {"result": result}


@router.post("/industry/hospitality/optimize-pricing")
async def hospitality_optimize_pricing(property_data: str, market_data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = HospitalityCopilot(db)
    result = await svc.optimize_pricing(property_data, market_data)
    return {"result": result}


@router.post("/industry/education/plan-lesson")
async def education_plan_lesson(subject: str, grade: str, topic: str, duration: int = 60, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EducationCopilot(db)
    result = await svc.plan_lesson(subject, grade, topic, duration)
    return {"result": result}


@router.post("/industry/education/create-assessment")
async def education_create_assessment(subject: str, grade: str, topic: str, question_count: int = 10, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EducationCopilot(db)
    result = await svc.create_assessment(subject, grade, topic, question_count, "multiple_choice,short_answer")
    return {"result": result}


@router.post("/industry/agriculture/plan-farming")
async def agriculture_plan_farming(farm_data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = AgricultureCopilot(db)
    result = await svc.plan_farming(farm_data)
    return {"result": result}


@router.post("/industry/agriculture/market-insights")
async def agriculture_market_insights(crop_type: str, region: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = AgricultureCopilot(db)
    result = await svc.market_insights(crop_type, region)
    return {"result": result}


@router.post("/industry/business/analyze-strategy")
async def business_analyze_strategy(company_data: str, market_data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = BusinessCopilot(db)
    result = await svc.analyze_strategy(company_data, market_data)
    return {"result": result}


@router.post("/industry/business/analyze-kpis")
async def business_analyze_kpis(kpi_data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = BusinessCopilot(db)
    result = await svc.analyze_kpis(kpi_data)
    return {"result": result}


@router.post("/industry/business/customer-insights")
async def business_customer_insights(customer_data: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = BusinessCopilot(db)
    result = await svc.customer_insights(customer_data)
    return {"result": result}


@router.post("/workflows", response_model=CopilotWorkflowResponse)
async def create_workflow(name: str, description: str, workflow_type: str, steps: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import json

    from app.models.v5_copilot import CopilotWorkflow
    wf = CopilotWorkflow(organization_id=current_user.organization_id or current_user.id, name=name, description=description, workflow_type=workflow_type, steps=json.loads(steps) if isinstance(steps, str) else steps, created_by=current_user.id)
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf


@router.post("/workflows/execute", response_model=CopilotWorkflowExecutionResponse)
async def execute_workflow(req: ExecuteWorkflowRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = CopilotEngine(db)
    result = await engine.execute_workflow(req.workflow_id, req.input_data)
    return result


@router.get("/workflows", response_model=list[CopilotWorkflowResponse])
async def list_workflows(industry: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    from app.models.v5_copilot import CopilotWorkflow
    q = select(CopilotWorkflow).where(CopilotWorkflow.organization_id == (current_user.organization_id or current_user.id))
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.post("/recommendations/generate", response_model=list[CopilotRecommendationResponse])
async def generate_recommendations(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = RecommendationEngine(db)
    return await engine.generate_recommendations(session_id, current_user.id, current_user.organization_id or current_user.id, "general")


@router.post("/approvals", response_model=CopilotApprovalResponse)
async def create_approval(req: ApprovalRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ApprovalService(db)
    return await svc.create_request(current_user.organization_id or current_user.id, current_user.id, req.request_type, req.description, req.details, req.session_id)


@router.get("/approvals/pending", response_model=list[CopilotApprovalResponse])
async def list_pending_approvals(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ApprovalService(db)
    return await svc.list_pending(current_user.organization_id or current_user.id)


@router.post("/approvals/{approval_id}/review")
async def review_approval(approval_id: uuid.UUID, decision: ApprovalDecision, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ApprovalService(db)
    result = await svc.review(approval_id, decision.approved, current_user.id, decision.reviewer_comment)
    return {"status": result.status if result else "not_found"}


@router.get("/analytics/dashboard")
async def copilot_analytics_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CopilotAnalyticsService(db)
    return await svc.get_dashboard(current_user.organization_id or current_user.id)

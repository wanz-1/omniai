from datetime import datetime, timezone
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.v6_governance import (
    AIEvaluation,
    AIDecision,
    HumanReview,
    PromptRegistry,
    PromptVersion,
    UserFeedback,
)
from app.schemas.v6_governance import (
    AIDecisionRecord,
    AIDecisionResponse,
    EvaluateRequest,
    EvaluateResponse,
    FeedbackResponse,
    FeedbackSubmit,
    GovernanceDashboardResponse,
    HallucinationCheckRequest,
    HallucinationCheckResponse,
    ModelSummaryResponse,
    PromptCreate,
    PromptResponse,
    PromptVersionCreate,
    PromptVersionResponse,
    QualityReportResponse,
    ReviewAction,
    ReviewActionResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.services.ai_governance.approval_workflows import ApprovalWorkflowService
from app.services.ai_governance.evaluation_engine import EvaluationEngine
from app.services.ai_governance.hallucination_detector import HallucinationDetector
from app.services.ai_governance.model_monitoring import ModelMonitoringService
from app.services.ai_governance.quality_scoring import QualityScoringService

router = APIRouter(prefix="/v6/governance", tags=["v6-governance"])


def _dbg(msg: str) -> None:
    print(f"[v6_governance] {msg}")


# ---------------------------------------------------------------------------
# Prompt Registry
# ---------------------------------------------------------------------------


@router.get("/prompts", response_model=list[PromptResponse])
async def list_prompts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    category: str = "",
    status: str = "",
):
    stmt = select(PromptRegistry)
    if category:
        stmt = stmt.where(PromptRegistry.category == category)
    if status:
        stmt = stmt.where(PromptRegistry.status == status)
    stmt = stmt.order_by(PromptRegistry.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.get(PromptRegistry, prompt_id)
    if not result:
        raise HTTPException(404, "Prompt not found")
    return result


@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(
    body: PromptCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    now = datetime.now(timezone.utc)
    prompt = PromptRegistry(
        name=body.name,
        category=body.category,
        description=body.description,
        owner=str(user.id),
        status="draft",
        current_version=0,
        created_at=now,
        updated_at=now,
    )
    db.add(prompt)
    await db.flush()

    version = PromptVersion(
        prompt_id=prompt.id,
        version=1,
        template=body.template,
        model_target=body.model_target or "",
        change_notes="Initial version",
        status="draft",
        parameters=body.parameters,
        created_by=str(user.id),
        created_at=now,
    )
    db.add(version)
    prompt.current_version = 1
    prompt.updated_at = now
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.get("/prompts/{prompt_id}/versions", response_model=list[PromptVersionResponse])
async def list_prompt_versions(
    prompt_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc())
    )
    return result.scalars().all()


@router.post("/prompts/{prompt_id}/versions", response_model=PromptVersionResponse)
async def create_prompt_version(
    prompt_id: uuid.UUID,
    body: PromptVersionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    prompt = await db.get(PromptRegistry, prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt not found")

    now = datetime.now(timezone.utc)
    new_version = prompt.current_version + 1
    version = PromptVersion(
        prompt_id=prompt_id,
        version=new_version,
        template=body.template,
        model_target=body.model_target or "",
        change_notes=body.change_notes or "",
        status="draft",
        parameters=body.parameters,
        created_by=str(user.id),
        created_at=now,
    )
    db.add(version)
    prompt.current_version = new_version
    prompt.updated_at = now
    await db.commit()
    await db.refresh(version)
    return version


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(
    body: EvaluateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    engine = EvaluationEngine(db)
    result = await engine.evaluate_response(
        model=body.model,
        input_text=body.input_text,
        output_text=body.output_text,
        case_id=body.case_id,
        prompt_version=body.prompt_version,
        expected_behavior=body.expected_behavior,
    )
    return result


@router.post("/hallucination-check", response_model=HallucinationCheckResponse)
async def check_hallucination(
    body: HallucinationCheckRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    detector = HallucinationDetector()
    result = await detector.analyze(
        text=body.text, source_text=body.source_text
    )
    return result


# ---------------------------------------------------------------------------
# Quality Reports
# ---------------------------------------------------------------------------


@router.get("/quality/{model}", response_model=QualityReportResponse)
async def quality_report(
    model: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    scorer = QualityScoringService(db)
    return await scorer.generate_quality_report(model)


# ---------------------------------------------------------------------------
# Model Monitoring
# ---------------------------------------------------------------------------


@router.get("/models", response_model=list[ModelSummaryResponse])
async def list_models(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    svc = ModelMonitoringService(db)
    return await svc.get_model_summary()


@router.get("/models/{model}", response_model=ModelSummaryResponse)
async def model_detail(
    model: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    svc = ModelMonitoringService(db)
    summaries = await svc.get_model_summary()
    result = next((s for s in summaries if s["model"] == model), None)
    if not result:
        raise HTTPException(404, "Model not found")
    return result


# ---------------------------------------------------------------------------
# Approval Workflows
# ---------------------------------------------------------------------------


@router.post("/reviews", response_model=ReviewResponse)
async def create_review(
    body: ReviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    svc = ApprovalWorkflowService(db)
    review = await svc.create_review_request(
        decision_id=body.decision_id,
        reviewer_id=body.reviewer_id,
        risk_level=body.risk_level,
        input_summary=body.input_summary,
        output_summary=body.output_summary,
    )
    return review


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    result = await db.get(HumanReview, review_id)
    if not result:
        raise HTTPException(404, "Review not found")
    return result


@router.post("/reviews/{review_id}/approve", response_model=ReviewActionResponse)
async def approve_review(
    review_id: uuid.UUID,
    body: ReviewAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    svc = ApprovalWorkflowService(db)
    result = await svc.approve(review_id=str(review_id), comments=body.comments)
    if not result:
        raise HTTPException(404, "Review not found or already resolved")
    return {"review_id": review_id, "status": "approved"}


@router.post("/reviews/{review_id}/reject", response_model=ReviewActionResponse)
async def reject_review(
    review_id: uuid.UUID,
    body: ReviewAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    svc = ApprovalWorkflowService(db)
    result = await svc.reject(review_id=str(review_id), comments=body.comments)
    if not result:
        raise HTTPException(404, "Review not found or already resolved")
    return {"review_id": review_id, "status": "rejected"}


# ---------------------------------------------------------------------------
# AI Decision Logging
# ---------------------------------------------------------------------------


@router.post("/decisions", response_model=AIDecisionResponse)
async def log_decision(
    body: AIDecisionRecord,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    now = datetime.now(timezone.utc)
    decision = AIDecision(
        user_id=uuid.UUID(body.user_id) if body.user_id else user.id,
        organization_id=body.organization_id,
        session_id=body.session_id,
        model=body.model,
        prompt_version=body.prompt_version,
        input_text=body.input_text,
        output_text=body.output_text,
        sources=body.sources,
        tools_used=body.tools_used,
        risk_level=body.risk_level,
        requires_review=body.requires_review,
        final_action=body.final_action,
        created_at=now,
    )
    db.add(decision)
    await db.commit()
    await db.refresh(decision)
    return decision


@router.get("/decisions", response_model=list[AIDecisionResponse])
async def list_decisions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=50, le=200),
):
    result = await db.execute(
        select(AIDecision)
        .order_by(AIDecision.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# User Feedback
# ---------------------------------------------------------------------------


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    body: FeedbackSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    now = datetime.now(timezone.utc)
    feedback = UserFeedback(
        user_id=user.id,
        decision_id=uuid.UUID(body.decision_id) if body.decision_id else None,
        model=body.model or "",
        rating=body.rating,
        rating_type=body.rating_type,
        correction=body.correction,
        comment=body.comment,
        category=body.category,
        created_at=now,
    )
    db.add(feedback)
    await db.commit()
    return {
        "id": feedback.id,
        "status": "received",
        "decision_id": feedback.decision_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "category": feedback.category,
        "created_at": feedback.created_at,
    }


# ---------------------------------------------------------------------------
# Dashboard Stats
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=GovernanceDashboardResponse)
async def governance_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    prompt_count = (await db.execute(select(func.count(PromptRegistry.id)))).scalar() or 0
    eval_count = (await db.execute(select(func.count(AIEvaluation.id)))).scalar() or 0
    review_count = (await db.execute(select(func.count(HumanReview.id)))).scalar() or 0
    feedback_count = (await db.execute(select(func.count(UserFeedback.id)))).scalar() or 0
    decision_count = (await db.execute(select(func.count(AIDecision.id)))).scalar() or 0

    passed_count = (
        await db.execute(
            select(func.count(AIEvaluation.id)).where(AIEvaluation.passed == True)
        )
    ).scalar() or 0

    return {
        "prompt_count": prompt_count,
        "evaluation_count": eval_count,
        "review_count": review_count,
        "feedback_count": feedback_count,
        "decision_count": decision_count,
        "passed_evaluations": passed_count,
        "health_score": round((passed_count / max(eval_count, 1)) * 100, 1),
    }

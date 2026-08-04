from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    name: str
    category: str
    template: str
    description: str = ""
    model_target: str = ""
    parameters: dict[str, Any] | None = None


class PromptVersionCreate(BaseModel):
    template: str
    change_notes: str = ""
    parameters: dict[str, Any] | None = None
    model_target: str = ""


class PromptResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: str
    owner: str | None
    current_version: int
    status: str
    created_at: datetime
    updated_at: datetime


class PromptVersionResponse(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    version: int
    template: str
    model_target: str | None
    change_notes: str | None
    status: str
    created_at: datetime


class EvaluateRequest(BaseModel):
    model: str
    input_text: str
    output_text: str
    case_id: str = ""
    prompt_version: str = ""
    expected_behavior: str = ""


class EvaluateResponse(BaseModel):
    id: uuid.UUID
    model: str
    accuracy_score: float | None
    safety_score: float | None
    citation_score: float | None
    issues: list[str] | None
    passed: bool
    created_at: datetime


class EvaluationCaseCreate(BaseModel):
    name: str
    category: str
    input: str
    expected_behavior: str
    difficulty: str = "medium"
    tags: list[str] | None = None


class QualityReportResponse(BaseModel):
    model: str
    total_evaluations: int
    failed_evaluations: int
    pass_rate: float
    scores: dict[str, float]


class ModelSummaryResponse(BaseModel):
    model: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    avg_quality_score: float | None


class ReviewRequest(BaseModel):
    decision_id: str
    reviewer_id: str
    risk_level: str = "medium"
    input_summary: str = ""
    output_summary: str = ""


class ReviewAction(BaseModel):
    comments: str = ""


class ReviewResponse(BaseModel):
    id: uuid.UUID
    decision_id: uuid.UUID | None = None
    reviewer_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    status: str = "pending"
    risk_level: str = "medium"
    input_summary: str | None = None
    output_summary: str | None = None
    decision: str | None = None
    comments: str | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    expires_at: datetime | None = None

    class Config:
        from_attributes = True


class ReviewActionResponse(BaseModel):
    review_id: uuid.UUID
    status: str


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    status: str = "received"
    decision_id: uuid.UUID | None = None
    rating: int | None = None
    comment: str | None = None
    category: str | None = None
    created_at: datetime | None = None


class GovernanceDashboardResponse(BaseModel):
    prompt_count: int
    evaluation_count: int
    review_count: int
    feedback_count: int
    decision_count: int
    passed_evaluations: int
    health_score: float


class AIDecisionRecord(BaseModel):
    user_id: str = ""
    organization_id: str = ""
    session_id: str = ""
    model: str
    prompt_version: str = ""
    input_text: str
    output_text: str
    sources: list[str] | None = None
    tools_used: list[str] | None = None
    risk_level: str = "low"
    requires_review: bool = False
    final_action: str = "completed"


class AIDecisionResponse(BaseModel):
    id: uuid.UUID
    model: str
    prompt_version: str | None
    risk_level: str
    requires_review: bool
    review_status: str
    final_action: str
    created_at: datetime


class FeedbackSubmit(BaseModel):
    decision_id: str = ""
    model: str
    rating: int = Field(ge=1, le=5, default=1)
    rating_type: str = "thumbs"
    correction: str = ""
    comment: str = ""
    category: str = ""


class HallucinationCheckRequest(BaseModel):
    text: str
    source_text: str = ""


class HallucinationCheckResponse(BaseModel):
    hallucination_count: int
    total_claims: int
    overall_confidence: float
    hallucination_rate: float

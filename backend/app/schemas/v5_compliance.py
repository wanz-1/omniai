import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RegulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID | None
    name: str
    jurisdiction: str
    category: str
    description: str
    requirements: list
    effective_date: datetime | None
    expiration_date: datetime | None
    is_active: bool
    source_url: str | None
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    policy_type: str
    description: str
    content: str
    status: str
    version: int
    compliance_score: float | None
    reviewed_at: datetime | None
    reviewed_by: uuid.UUID | None
    effective_date: datetime | None
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class ComplianceCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    check_type: str
    status: str
    scope: list
    results_summary: dict
    started_by: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ComplianceCheckResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    check_id: uuid.UUID
    item_type: str
    item_id: uuid.UUID | None
    status: str
    finding: str | None
    severity: str
    score: float | None
    details: dict | None
    created_at: datetime
    updated_at: datetime


class AuditRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    audit_type: str
    title: str
    description: str
    scope: list
    status: str
    auditor: str | None
    audit_date: datetime | None
    completed_date: datetime | None
    findings_summary: dict | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    audit_id: uuid.UUID | None
    organization_id: uuid.UUID
    finding_type: str
    title: str
    description: str
    severity: str
    status: str
    source: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CorrectiveActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID | None
    organization_id: uuid.UUID
    title: str
    description: str
    action_plan: str
    priority: str
    status: str
    assigned_to: uuid.UUID | None
    deadline: datetime | None
    completed_at: datetime | None
    verification_notes: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RiskScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    score_type: str
    score: float
    max_score: float
    category: str | None
    details: dict | None
    assessed_at: datetime
    assessed_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ComplianceReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    report_type: str
    content: dict
    generated_by: uuid.UUID
    generated_at: datetime
    period_start: datetime | None
    period_end: datetime | None
    created_at: datetime
    updated_at: datetime


class ApprovalHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    requester_id: uuid.UUID
    reviewer_id: uuid.UUID | None
    action_type: str
    target_type: str
    target_id: uuid.UUID | None
    status: str
    comment: str | None
    created_at: datetime
    resolved_at: datetime | None
    updated_at: datetime


class IndustryCompliancePackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID | None
    industry: str
    name: str
    description: str
    requirements: list
    policies: list
    checks: list
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ComplianceDocumentReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    document_id: uuid.UUID | None
    document_type: str
    title: str
    content: str
    review_status: str
    issues: list
    score: float | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class RegulatoryUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID | None
    regulation_id: uuid.UUID | None
    title: str
    description: str
    change_type: str
    impact: str
    affected_areas: list
    recommended_actions: str | None
    detected_at: datetime
    is_reviewed: bool
    created_at: datetime
    updated_at: datetime


class AnalyzeDocumentRequest(BaseModel):
    content: str
    document_type: str
    title: str


class CheckPolicyRequest(BaseModel):
    policy_id: uuid.UUID | None = None
    content: str | None = None


class CreateAuditRequest(BaseModel):
    audit_type: str
    title: str
    description: str
    scope: list | None = None


class CreateFindingRequest(BaseModel):
    audit_id: uuid.UUID | None = None
    finding_type: str
    title: str
    description: str
    severity: str


class CreateCorrectiveActionRequest(BaseModel):
    finding_id: uuid.UUID | None = None
    title: str
    description: str
    action_plan: str
    priority: str
    assigned_to: uuid.UUID | None = None
    deadline: str | None = None


class ComplianceQuery(BaseModel):
    query: str
    context: dict | None


class ReviewDocumentRequest(BaseModel):
    title: str
    content: str
    document_type: str


class ApprovalDecision(BaseModel):
    approved: bool
    comment: str | None

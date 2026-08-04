import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class AgentQueryRequest(BaseModel):
    agent_type: str
    query: str
    organization_id: uuid.UUID
    context: dict | None = None


class AgentQueryResponse(BaseModel):
    response: str
    agent_type: str
    suggestions: list[str] = []
    context_used: dict = {}


class BusinessMetricResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_type: str
    metric_key: str
    metric_name: str
    value: float
    currency: str | None = None
    unit: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    source: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class BusinessReportResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_type: str
    report_type: str
    title: str
    summary: str | None = None
    recommendations: list | None = None
    content: dict | None = None
    status: str = "completed"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ApprovalRequestCreate(BaseModel):
    organization_id: uuid.UUID
    request_type: str
    title: str
    description: str | None = None
    priority: str = "medium"
    payload: dict | None = None


class ApprovalRequestResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    request_type: str
    title: str
    description: str | None = None
    requester_id: uuid.UUID
    approver_id: uuid.UUID | None = None
    status: str
    priority: str
    decision_notes: str | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None

    class Config:
        from_attributes = True


class FinancialRecordCreate(BaseModel):
    organization_id: uuid.UUID
    record_type: str
    category: str
    amount: float
    description: str | None = None
    currency: str = "USD"
    transaction_date: datetime | None = None
    reference: str | None = None
    donor: str | None = None
    grant_code: str | None = None
    budget_line: str | None = None


class FinancialRecordResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    record_type: str
    category: str
    description: str | None = None
    amount: float
    currency: str
    transaction_date: datetime | None = None
    reference: str | None = None
    donor: str | None = None
    grant_code: str | None = None
    budget_line: str | None = None
    approval_status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class KnowledgeDocumentCreate(BaseModel):
    organization_id: uuid.UUID
    title: str
    content: str
    doc_type: str | None = None
    source: str | None = None
    tags: list[str] | None = None


class KnowledgeDocumentResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    content: str | None = None
    doc_type: str | None = None
    source: str | None = None
    tags: list | None = None
    is_active: bool = True
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class WorkflowStep(BaseModel):
    type: str
    name: str
    config: dict = {}


class WorkflowCreateRequest(BaseModel):
    organization_id: uuid.UUID
    name: str
    workflow_type: str
    trigger: str
    steps: list[dict]


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    workflow_type: str
    trigger: str
    steps: list | None = None
    is_active: bool = True
    last_run_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    current_step: int | None = None
    total_steps: int | None = None
    output_data: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True

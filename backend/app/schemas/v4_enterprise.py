import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeConnectorResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    connector_type: str
    config: dict | None = None
    status: str
    last_sync_at: datetime | None = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class KnowledgeSourceResponse(BaseModel):
    id: uuid.UUID
    connector_id: uuid.UUID
    name: str
    source_type: str
    total_documents: int = 0
    last_indexed_at: datetime | None = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class EnterpriseDocumentResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    file_type: str | None = None
    url: str | None = None
    author: str | None = None
    indexed_at: datetime | None = None
    is_indexed: bool = False
    model_config = ConfigDict(from_attributes=True)


class AIPolicyResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    policy_type: str
    rules: dict | None = None
    scope: str | None = None
    severity: str = "medium"
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class AgentApprovalRequestResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_name: str
    requested_by: str
    capabilities: list | None = None
    justification: str | None = None
    status: str = "pending"
    model_config = ConfigDict(from_attributes=True)


class AIAuditEventResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    event_type: str
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    details: dict | None = None
    severity: str
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AIMonitoringEventV4Response(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    event_type: str
    model_id: str
    model_provider: str
    latency_ms: float = 0.0
    cost: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    status: str
    error_message: str | None = None
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ObservabilityDashboardResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    dashboard_type: str
    config: dict | None = None
    is_default: bool = False
    model_config = ConfigDict(from_attributes=True)


class EnterpriseAnalyticsV4Response(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    metric_category: str
    metric_name: str
    metric_value: float
    unit: str | None = None
    period: str
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdoptionMetricV4Response(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    feature_name: str
    total_users: int = 0
    active_users: int = 0
    adoption_rate: float = 0.0
    period: str
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CostSavingsRecordV4Response(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    category: str
    description: str | None = None
    amount_saved: float
    currency: str
    period: str
    model_config = ConfigDict(from_attributes=True)


class PolicyCheckRequest(BaseModel):
    policy_type: str
    resource_type: str
    action: str
    context: dict | None = None


class PolicyCheckResponse(BaseModel):
    allowed: bool
    policy_name: str | None = None
    reason: str | None = None
    required_approvals: list | None = None

import uuid
from datetime import datetime
from pydantic import BaseModel


class CopilotConfigResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; industry: str; name: str
    description: str | None = None; is_active: bool = True
    created_by: uuid.UUID
    class Config: from_attributes = True


class CopilotSessionResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; user_id: uuid.UUID
    copilot_id: uuid.UUID; title: str; status: str = "active"
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True


class CopilotMessageResponse(BaseModel):
    id: uuid.UUID; session_id: uuid.UUID; role: str
    content: str | None = None; tool_calls: dict | None = None
    tool_results: dict | None = None; meta_data: dict | None = None
    created_at: datetime
    class Config: from_attributes = True


class CopilotWorkflowResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; copilot_id: uuid.UUID
    name: str; description: str | None = None; workflow_type: str
    is_active: bool = True; created_by: uuid.UUID
    class Config: from_attributes = True


class CopilotWorkflowExecutionResponse(BaseModel):
    id: uuid.UUID; workflow_id: uuid.UUID; organization_id: uuid.UUID
    user_id: uuid.UUID; status: str; input_data: dict | None = None
    output_data: dict | None = None; error: str | None = None
    started_at: datetime | None = None; completed_at: datetime | None = None
    class Config: from_attributes = True


class CopilotRecommendationResponse(BaseModel):
    id: uuid.UUID; session_id: uuid.UUID; organization_id: uuid.UUID
    user_id: uuid.UUID; industry: str; recommendation_type: str
    title: str; description: str | None = None
    confidence: float | None = None; data: dict | None = None
    applied: bool = False; created_at: datetime
    class Config: from_attributes = True


class CopilotApprovalResponse(BaseModel):
    id: uuid.UUID; session_id: uuid.UUID; organization_id: uuid.UUID
    requester_id: uuid.UUID; reviewer_id: uuid.UUID | None = None
    request_type: str; description: str | None = None
    details: dict | None = None; status: str
    reviewer_comment: str | None = None; created_at: datetime
    resolved_at: datetime | None = None
    class Config: from_attributes = True


class CopilotAnalyticResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; copilot_id: uuid.UUID
    user_id: uuid.UUID; event_type: str; details: dict | None = None
    created_at: datetime
    class Config: from_attributes = True


class CopilotDomainRuleResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; industry: str
    rule_type: str; name: str; description: str | None = None
    conditions: dict | None = None; actions: dict | None = None
    severity: str = "info"; is_active: bool = True
    class Config: from_attributes = True


class CopilotKnowledgeLinkResponse(BaseModel):
    id: uuid.UUID; copilot_id: uuid.UUID
    document_id: uuid.UUID | None = None
    connector_id: uuid.UUID | None = None
    organization_id: uuid.UUID; is_active: bool = True
    class Config: from_attributes = True


class CopilotChatRequest(BaseModel):
    session_id: uuid.UUID | None = None
    copilot_id: uuid.UUID
    message: str
    context: dict | None = None


class CopilotChatResponse(BaseModel):
    session_id: str
    reply: str
    recommendations: list | None = None
    actions: list | None = None


class ExecuteWorkflowRequest(BaseModel):
    workflow_id: uuid.UUID
    input_data: dict


class ApprovalRequest(BaseModel):
    request_type: str
    description: str
    details: dict
    session_id: uuid.UUID | None = None


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer_comment: str | None = None


class CopilotQueryRequest(BaseModel):
    query: str
    industry: str
    copilot_id: uuid.UUID | None = None

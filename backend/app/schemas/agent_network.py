import uuid
from datetime import datetime
from pydantic import BaseModel


class AgentTeamCreate(BaseModel):
    name: str
    description: str | None = None
    purpose: str | None = None
    icon: str | None = None
    color: str | None = None
    config: dict | None = None
    organization_id: uuid.UUID | None = None


class AgentTeamMemberAdd(BaseModel):
    agent_id: uuid.UUID
    role: str
    responsibilities: str | None = None
    is_lead: bool = False
    order: int = 0


class AgentTeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    purpose: str | None = None
    is_active: bool
    is_template: bool
    icon: str | None = None
    color: str | None = None
    config: dict | None = None
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    members: list | None = None

    class Config:
        from_attributes = True


class AgentMessageResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    content: str
    message_type: str
    status: str
    meta_data: dict | None = None
    task_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    read_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AgentTaskDelegationCreate(BaseModel):
    title: str
    description: str | None = None
    priority: int = 1
    deadline: datetime | None = None
    input_data: dict | None = None
    assignee_id: uuid.UUID
    team_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None


class AgentTaskDelegationResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    priority: int
    progress: float
    assignor_id: uuid.UUID
    assignee_id: uuid.UUID
    team_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None
    input_data: dict | None = None
    output_data: dict | None = None
    result_summary: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AgentReviewCreate(BaseModel):
    reviewee_id: uuid.UUID
    score: float
    content: str | None = None
    review_type: str = "peer"
    criteria_scores: dict | None = None
    confidence: float | None = None
    suggestions: list[str] | None = None
    task_id: uuid.UUID | None = None


class AgentReviewResponse(BaseModel):
    id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewee_id: uuid.UUID
    score: float
    content: str | None = None
    review_type: str
    criteria_scores: dict | None = None
    confidence: float | None = None
    suggestions: list | None = None
    is_approved: bool
    task_id: uuid.UUID | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class OrchestrateRequest(BaseModel):
    organization_id: uuid.UUID
    task: str
    team_config: dict | None = None
    context: dict | None = None


class OrchestrateResponse(BaseModel):
    final_output: str
    team_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    steps_completed: int = 0
    agents_involved: list[str] = []
    execution_log: list | None = None


class ResearchRequest(BaseModel):
    title: str
    topic: str
    depth: str = "standard"
    organization_id: uuid.UUID | None = None
    context: str | None = None


class ResearchResponse(BaseModel):
    id: uuid.UUID
    title: str
    topic: str
    depth: str
    status: str
    summary: str | None = None
    findings: dict | None = None
    recommendations: list | None = None
    confidence: float | None = None

    class Config:
        from_attributes = True


class DevProjectRequest(BaseModel):
    name: str
    description: str | None = None
    tech_stack: list[str] | None = None
    requirements: str | None = None
    organization_id: uuid.UUID | None = None


class DevProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    tech_stack: list | None = None
    status: str
    requirements: dict | None = None
    architecture: dict | None = None
    progress: float
    team_id: uuid.UUID | None = None
    repo_url: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    agent_id: uuid.UUID
    resource: str
    action: str
    access_level: str = "allow"
    conditions: dict | None = None
    team_id: uuid.UUID | None = None


class PermissionResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    resource: str
    action: str
    access_level: str
    conditions: dict | None = None
    is_active: bool
    team_id: uuid.UUID | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class MemoryNetworkCreate(BaseModel):
    key: str
    content: str
    memory_type: str = "fact"
    category: str | None = None
    importance: int = 1
    visibility: str = "team"
    source: str | None = None
    team_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None


class MemoryNetworkResponse(BaseModel):
    id: uuid.UUID
    key: str
    content: str
    memory_type: str
    category: str | None = None
    importance: int
    visibility: str
    source: str | None = None
    team_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class GovernanceAuditLog(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID | None = None
    action: str
    resource: str
    status: str
    details: dict | None = None
    timestamp: datetime

    class Config:
        from_attributes = True

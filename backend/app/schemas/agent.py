import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    proficiency: int = 5


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    category: str | None = None
    proficiency: int
    agent_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    memory_type: str = "fact"
    category: str | None = None
    importance: int = 1
    is_organization: bool = False


class MemoryResponse(BaseModel):
    id: uuid.UUID
    key: str
    content: str
    memory_type: str
    category: str | None = None
    importance: int
    is_organization: bool
    agent_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tool_type: str = Field(..., min_length=1)
    description: str | None = None
    config: dict | None = None
    enabled: bool = True


class ToolResponse(BaseModel):
    id: uuid.UUID
    name: str
    tool_type: str
    description: str | None = None
    config: dict | None = None
    enabled: bool
    agent_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowStepCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    step_type: str = Field(..., min_length=1)
    config: dict | None = None
    order: int = 0
    position_x: float | None = None
    position_y: float | None = None


class WorkflowStepResponse(BaseModel):
    id: uuid.UUID
    name: str
    step_type: str
    config: dict | None = None
    order: int
    position_x: float | None = None
    position_y: float | None = None
    workflow_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    trigger_event: str | None = None
    trigger_config: dict | None = None
    steps: list[WorkflowStepCreate] = []


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    is_active: bool
    trigger_event: str | None = None
    trigger_config: dict | None = None
    agent_id: uuid.UUID
    steps: list[WorkflowStepResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    system_prompt: str | None = None
    model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    icon: str | None = None
    color: str | None = None
    skills: list[SkillCreate] = []
    tools: list[ToolCreate] = []


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    role: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    status: str | None = None
    icon: str | None = None
    color: str | None = None
    config: dict | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    description: str | None = None
    system_prompt: str | None = None
    model: str
    temperature: float
    status: str
    is_template: bool
    template_category: str | None = None
    icon: str | None = None
    color: str | None = None
    config: dict | None = None
    published: bool
    marketplace_listed: bool
    price: float | None = None
    download_count: int
    user_id: uuid.UUID
    skills: list[SkillResponse] = []
    tools: list[ToolResponse] = []
    workflows: list[WorkflowResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    priority: int = 1
    input_data: dict | None = None


class AgentTaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    priority: int
    progress: float
    result: str | None = None
    error: str | None = None
    input_data: dict | None = None
    output_data: dict | None = None
    execution_plan: dict | None = None
    agent_id: uuid.UUID
    user_id: uuid.UUID
    parent_task_id: uuid.UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    tokens_used: int
    steps_completed: int
    steps_total: int
    input: str | None = None
    output: str | None = None
    error: str | None = None
    execution_log: list | None = None
    agent_id: uuid.UUID
    task_id: uuid.UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionStreamEvent(BaseModel):
    type: str
    content: str
    step: str | None = None
    progress: float | None = None


class AgentAnalyticsResponse(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    avg_duration_ms: float | None = None
    avg_satisfaction: float | None = None
    top_skills: list | None = None
    daily_usage: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    stream: bool = False


class AgentChatResponse(BaseModel):
    reply: str
    tokens_used: int = 0
    execution_id: uuid.UUID | None = None

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    proficiency: int = 5


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    proficiency: int
    agent_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    memory_type: str = "fact"
    category: Optional[str] = None
    importance: int = 1
    is_organization: bool = False


class MemoryResponse(BaseModel):
    id: uuid.UUID
    key: str
    content: str
    memory_type: str
    category: Optional[str] = None
    importance: int
    is_organization: bool
    agent_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tool_type: str = Field(..., min_length=1)
    description: Optional[str] = None
    config: Optional[dict] = None
    enabled: bool = True


class ToolResponse(BaseModel):
    id: uuid.UUID
    name: str
    tool_type: str
    description: Optional[str] = None
    config: Optional[dict] = None
    enabled: bool
    agent_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowStepCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    step_type: str = Field(..., min_length=1)
    config: Optional[dict] = None
    order: int = 0
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class WorkflowStepResponse(BaseModel):
    id: uuid.UUID
    name: str
    step_type: str
    config: Optional[dict] = None
    order: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    workflow_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    trigger_event: Optional[str] = None
    trigger_config: Optional[dict] = None
    steps: list[WorkflowStepCreate] = []


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    trigger_event: Optional[str] = None
    trigger_config: Optional[dict] = None
    agent_id: uuid.UUID
    steps: list[WorkflowStepResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    icon: Optional[str] = None
    color: Optional[str] = None
    skills: list[SkillCreate] = []
    tools: list[ToolCreate] = []


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    status: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    config: Optional[dict] = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: str
    temperature: float
    status: str
    is_template: bool
    template_category: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    config: Optional[dict] = None
    published: bool
    marketplace_listed: bool
    price: Optional[float] = None
    download_count: int
    user_id: uuid.UUID
    skills: list[SkillResponse] = []
    tools: list[ToolResponse] = []
    workflows: list[WorkflowResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    priority: int = 1
    input_data: Optional[dict] = None


class AgentTaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: int
    progress: float
    result: Optional[str] = None
    error: Optional[str] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    execution_plan: Optional[dict] = None
    agent_id: uuid.UUID
    user_id: uuid.UUID
    parent_task_id: Optional[uuid.UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    tokens_used: int
    steps_completed: int
    steps_total: int
    input: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    execution_log: Optional[list] = None
    agent_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionStreamEvent(BaseModel):
    type: str
    content: str
    step: Optional[str] = None
    progress: Optional[float] = None


class AgentAnalyticsResponse(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    avg_duration_ms: Optional[float] = None
    avg_satisfaction: Optional[float] = None
    top_skills: Optional[list] = None
    daily_usage: Optional[dict] = None

    class Config:
        from_attributes = True


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    stream: bool = False


class AgentChatResponse(BaseModel):
    reply: str
    tokens_used: int = 0
    execution_id: Optional[uuid.UUID] = None

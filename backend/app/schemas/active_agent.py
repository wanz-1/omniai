"""Schemas for Active AI Agents."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.active_agent import ActiveAgentMode


class ActiveAgentCreate(BaseModel):
    agent_id: uuid.UUID = Field(..., description="Base AgentProfile to activate")
    name: str | None = Field(None, description="Optional instance name, defaults to agent name + timestamp")
    mode: ActiveAgentMode = Field(default=ActiveAgentMode.CONTINUOUS)
    organization_id: uuid.UUID | None = None
    config: dict | None = Field(default=None, description="Runtime config overrides")
    cron_schedule: str | None = Field(None, description="Cron expression for scheduled mode, e.g. '*/5 * * * *'")


class ActiveAgentUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    cron_schedule: str | None = None


class ActiveAgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    agent_id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID | None
    status: str
    mode: str
    is_active: bool
    config: dict | None
    heartbeat_at: datetime | None
    started_at: datetime | None
    stopped_at: datetime | None
    paused_at: datetime | None
    current_task_id: uuid.UUID | None
    last_error: str | None
    run_count: int
    total_tasks_completed: int
    total_tokens_used: int
    cron_schedule: str | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Embedded agent info for convenience
    agent_name: str | None = None
    agent_role: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ActiveAgentLogResponse(BaseModel):
    id: uuid.UUID
    active_agent_id: uuid.UUID
    agent_id: uuid.UUID
    level: str
    event_type: str
    message: str
    data: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActiveAgentHeartbeat(BaseModel):
    status: str
    heartbeat_at: datetime
    current_task_id: uuid.UUID | None = None
    message: str | None = None


class ActivateRequest(BaseModel):
    mode: ActiveAgentMode = Field(default=ActiveAgentMode.CONTINUOUS)
    config: dict | None = None
    name: str | None = None
    organization_id: uuid.UUID | None = None
    cron_schedule: str | None = None


class TaskAssignRequest(BaseModel):
    title: str
    description: str | None = None
    priority: int = Field(default=1, ge=1, le=5)
    input_data: dict | None = None


class ActiveAgentStatsResponse(BaseModel):
    total_active: int
    running: int
    idle: int
    paused: int
    error: int
    total_runs: int
    total_tasks_completed: int


# ─── Goals ─────────────────────────────────────────────────────────────────

class ActiveAgentGoalCreate(BaseModel):
    title: str = Field(..., max_length=300)
    description: str | None = None
    priority: int = Field(default=1, ge=1, le=5)
    success_criteria: dict | None = None
    deadline_at: datetime | None = None


class ActiveAgentGoalResponse(BaseModel):
    id: uuid.UUID
    active_agent_id: uuid.UUID
    agent_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: int
    progress: float
    success_criteria: dict | None
    deadline_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActiveAgentGoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = None
    progress: float | None = Field(None, ge=0.0, le=1.0)
    success_criteria: dict | None = None


# ─── Memory ────────────────────────────────────────────────────────────────

class ActiveAgentMemoryCreate(BaseModel):
    key: str
    content: str
    memory_type: str = Field(default="episodic")
    importance: int = Field(default=1, ge=1, le=10)


class ActiveAgentMemoryResponse(BaseModel):
    id: uuid.UUID
    active_agent_id: uuid.UUID
    agent_id: uuid.UUID
    key: str
    content: str
    memory_type: str
    importance: int
    access_count: int
    last_accessed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PersonalAssistantResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    personality: str | None = None
    capabilities: list | None = None
    is_active: bool = True
    total_interactions: int = 0
    last_interaction: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PersonalMemoryResponse(BaseModel):
    id: uuid.UUID
    memory_type: str
    title: str | None = None
    content: str | None = None
    summary: str | None = None
    importance: int = 0
    tags: list | None = None
    is_archived: bool = False
    model_config = ConfigDict(from_attributes=True)


class PersonalTaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    status: str = "pending"
    priority: str = "medium"
    due_date: datetime | None = None
    category: str | None = None
    completed_at: datetime | None = None
    ai_generated: bool = False
    model_config = ConfigDict(from_attributes=True)


class ExecutiveAssistantResponse(BaseModel):
    id: uuid.UUID
    role: str
    name: str
    description: str | None = None
    capabilities: list | None = None
    is_active: bool = True
    insights: list | None = None
    recommendations: list | None = None
    model_config = ConfigDict(from_attributes=True)


class PersonalQuery(BaseModel):
    assistant_id: uuid.UUID
    query: str
    context: dict | None = None


class PersonalQueryResponse(BaseModel):
    response: str
    sources: list | None = None
    actions_taken: list | None = None

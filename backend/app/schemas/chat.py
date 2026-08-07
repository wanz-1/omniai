import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreateRequest(BaseModel):
    title: str = "New Chat"
    model: str = "gpt-4o"
    system_prompt: str | None = None


class ChatSessionUpdateRequest(BaseModel):
    title: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    is_archived: bool | None = None


class ChatMessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1)
    stream: bool = True


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    tokens_used: int | None = None
    latency_ms: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    model: str
    system_prompt: str | None = None
    is_archived: bool
    user_id: uuid.UUID
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

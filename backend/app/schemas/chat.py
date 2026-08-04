import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatSessionCreateRequest(BaseModel):
    title: str = "New Chat"
    model: str = "gpt-4o"
    system_prompt: Optional[str] = None


class ChatSessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    is_archived: Optional[bool] = None


class ChatMessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1)
    stream: bool = True


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    model: str
    system_prompt: Optional[str] = None
    is_archived: bool
    user_id: uuid.UUID
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

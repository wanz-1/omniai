import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VoiceSessionCreateRequest(BaseModel):
    organization_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    language: str = "en"


class VoiceMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    text: str | None = None
    audio_url: str | None = None
    duration_ms: int | None = None
    confidence: float | None = None
    language: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class VoiceSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    status: str
    duration_ms: int | None = None
    language: str = "en"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    ended_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

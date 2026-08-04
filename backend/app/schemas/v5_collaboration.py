import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CollaborationSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    session_type: str
    status: str
    description: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_by: uuid.UUID
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class SessionParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime | None
    left_at: datetime | None
    is_present: bool
    created_at: datetime
    updated_at: datetime


class MultimodalMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    sender_id: uuid.UUID
    message_type: str
    content: str | None
    media_url: str | None
    media_type: str | None
    duration_seconds: float | None
    transcript: str | None
    parent_id: uuid.UUID | None
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class WhiteboardSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    title: str
    canvas_data: dict
    strokes: list
    shapes: list
    annotations: list
    width: int
    height: int
    is_locked: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SessionRecordingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    recording_type: str
    file_url: str | None
    duration_seconds: float | None
    file_size: int | None
    status: str
    transcript: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AIMeetingInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    organization_id: uuid.UUID
    summary: str | None
    transcript_full: str | None
    action_items: list
    decisions: list
    topics: list
    sentiment: str | None
    key_insights: list
    participants_summary: list
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class CollaborationAgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    agent_type: str
    capabilities: list
    config: dict
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ScreenShareSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    host_id: uuid.UUID
    stream_url: str | None
    is_active: bool
    started_at: datetime
    ended_at: datetime | None
    recording_url: str | None
    created_at: datetime
    updated_at: datetime


class DocumentCollaborationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    document_id: uuid.UUID
    document_type: str
    title: str
    content: dict
    version: int
    is_locked: bool
    locked_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CreateSessionRequest(BaseModel):
    title: str
    session_type: str
    description: str | None
    participants: list[uuid.UUID] | None


class SendMessageRequest(BaseModel):
    session_id: uuid.UUID
    message_type: str
    content: str | None
    media_url: str | None
    media_type: str | None
    duration_seconds: float | None
    parent_id: uuid.UUID | None


class CreateWhiteboardRequest(BaseModel):
    session_id: uuid.UUID
    title: str


class UpdateWhiteboardRequest(BaseModel):
    strokes: list | None
    shapes: list | None
    annotations: list | None


class CreateAgentRequest(BaseModel):
    name: str
    agent_type: str
    capabilities: list | None
    config: dict | None


class JoinAgentRequest(BaseModel):
    session_id: uuid.UUID
    agent_id: uuid.UUID
    role: str | None


class CollaborationDashboardResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    total_participants: int
    total_messages: int
    total_recordings: int
    total_whiteboards: int
    by_type: dict

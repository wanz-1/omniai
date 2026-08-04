import uuid
from datetime import datetime
from pydantic import BaseModel


class MeetingSessionResponse(BaseModel):
    id: uuid.UUID; title: str; description: str | None = None
    participants: list | None = None; duration_minutes: int | None = None
    status: str = "scheduled"; summary: str | None = None
    decisions: list | None = None; action_items: list | None = None
    class Config: from_attributes = True


class CommunicationResponse(BaseModel):
    id: uuid.UUID; communication_type: str; title: str
    content: str | None = None; recipient: str | None = None
    tone: str | None = None; status: str = "draft"
    generated_content: str | None = None
    class Config: from_attributes = True


class LearningPathResponse(BaseModel):
    id: uuid.UUID; title: str; description: str | None = None
    subject: str | None = None; skill_level: str = "beginner"
    goals: list | None = None; progress: float = 0.0
    modules: list | None = None; status: str = "active"
    class Config: from_attributes = True


class PhysicalDeviceResponse(BaseModel):
    id: uuid.UUID; name: str; device_type: str; protocol: str = "mqtt"
    status: str = "disconnected"; capabilities: list | None = None
    last_seen: datetime | None = None; is_active: bool = True
    class Config: from_attributes = True


class DeviceTelemetryResponse(BaseModel):
    id: uuid.UUID; device_id: uuid.UUID; metric_name: str
    metric_value: float; unit: str | None = None; recorded_at: datetime
    class Config: from_attributes = True


class MeetingAnalysisRequest(BaseModel):
    title: str; transcript: str; participants: list[str] | None = None


class MeetingAnalysisResponse(BaseModel):
    summary: str; decisions: list[str]; action_items: list[str]; key_topics: list[str]

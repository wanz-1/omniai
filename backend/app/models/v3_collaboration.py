import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AIMeetingSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_meeting_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    participants: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    decisions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    action_items: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    key_topics: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    recording_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"AIMeetingSession(id={self.id}, title={self.title})"


class AICommunication(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_communications"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    communication_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(300), nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    generated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    ai_suggestions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self):
        return f"AICommunication(id={self.id}, title={self.title})"


class LearningPath(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "learning_paths"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(200), nullable=True)
    skill_level: Mapped[str] = mapped_column(String(20), default="beginner", nullable=False)
    goals: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    modules: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    resources: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    certificates: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    def __repr__(self):
        return f"LearningPath(id={self.id}, title={self.title})"


class PhysicalDevice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "physical_devices"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    protocol: Mapped[str] = mapped_column(String(50), default="mqtt", nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    credentials: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="disconnected", nullable=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    schedules = relationship("DeviceSchedule", back_populates="device", cascade="all, delete-orphan")
    telemetry = relationship("DeviceTelemetry", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"PhysicalDevice(id={self.id}, name={self.name})"


class DeviceSchedule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "device_schedules"

    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("physical_devices.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    device = relationship("PhysicalDevice", back_populates="schedules")

    def __repr__(self):
        return f"DeviceSchedule(id={self.id}, name={self.name})"


class DeviceTelemetry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "device_telemetry"

    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("physical_devices.id"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    device = relationship("PhysicalDevice", back_populates="telemetry")

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MediaType, VideoJobStatus, VoiceSessionStatus
from app.models.base import Base, TimestampMixin, UUIDMixin


class VoiceSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "voice_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=True
    )
    status: Mapped[VoiceSessionStatus] = mapped_column(
        Enum(VoiceSessionStatus), default=VoiceSessionStatus.ACTIVE, nullable=False
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    transcription: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages = relationship("VoiceMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"VoiceSession(id={self.id}, status={self.status})"


class VoiceMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "voice_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("voice_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    session = relationship("VoiceSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"VoiceMessage(id={self.id}, role={self.role})"


class MediaAsset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "media_assets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    asset_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType), nullable=False
    )
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_tags: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    ai_analysis: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self) -> str:
        return f"MediaAsset(id={self.id}, type={self.asset_type})"


class OCRResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ocr_results"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id"), nullable=False, index=True
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    pages: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    asset = relationship("MediaAsset")

    def __repr__(self) -> str:
        return f"OCRResult(id={self.id}, asset={self.asset_id})"


class VideoJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "video_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    input_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[VideoJobStatus] = mapped_column(
        Enum(VideoJobStatus), default=VideoJobStatus.PENDING, nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"VideoJob(id={self.id}, type={self.job_type}, status={self.status})"


class MultimodalConversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "multimodal_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    modality: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    messages = relationship("MediaMultimodalMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"MultimodalConversation(id={self.id})"


class MediaMultimodalMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "multimodal_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("multimodal_conversations.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_asset_ids: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    conversation = relationship("MultimodalConversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"MediaMultimodalMessage(id={self.id}, role={self.role})"

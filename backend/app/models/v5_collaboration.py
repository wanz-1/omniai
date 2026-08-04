import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class CollaborationSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "collaboration_sessions"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    session_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("MultimodalMessage", back_populates="session", cascade="all, delete-orphan")
    whiteboards = relationship("WhiteboardSession", back_populates="session", cascade="all, delete-orphan")
    recordings = relationship("SessionRecording", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CollaborationSession {self.title} ({self.session_type})>"


class SessionParticipant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "session_participants"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="participant")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_present: Mapped[bool] = mapped_column(Boolean, default=False)

    session = relationship("CollaborationSession", back_populates="participants")

    def __repr__(self):
        return f"<SessionParticipant user={self.user_id} role={self.role}>"


class MultimodalMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "collab_multimodal_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    media_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    session = relationship("CollaborationSession", back_populates="messages")

    def __repr__(self):
        return f"<MultimodalMessage {self.message_type} by {self.sender_id}>"


class WhiteboardSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "whiteboard_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    canvas_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    strokes: Mapped[list] = mapped_column(JSONB, default=list)
    shapes: Mapped[list] = mapped_column(JSONB, default=list)
    annotations: Mapped[list] = mapped_column(JSONB, default=list)
    width: Mapped[int] = mapped_column(Integer, default=1920)
    height: Mapped[int] = mapped_column(Integer, default=1080)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    session = relationship("CollaborationSession", back_populates="whiteboards")

    def __repr__(self):
        return f"<WhiteboardSession {self.title}>"


class SessionRecording(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "session_recordings"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    recording_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="recording")
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session = relationship("CollaborationSession", back_populates="recordings")

    def __repr__(self):
        return f"<SessionRecording {self.recording_type}>"


class AIMeetingInsight(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_meeting_insights"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_full: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[list] = mapped_column(JSONB, default=list)
    decisions: Mapped[list] = mapped_column(JSONB, default=list)
    topics: Mapped[list] = mapped_column(JSONB, default=list)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    key_insights: Mapped[list] = mapped_column(JSONB, default=list)
    participants_summary: Mapped[list] = mapped_column(JSONB, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<AIMeetingInsight session={self.session_id}>"


class CollaborationAgent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "collaboration_agents"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    capabilities: Mapped[list] = mapped_column(JSONB, default=list)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    sessions = relationship("AgentSessionLink", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CollaborationAgent {self.name} ({self.agent_type})>"


class AgentSessionLink(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_session_links"

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_agents.id"), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), default="assistant")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    agent = relationship("CollaborationAgent", back_populates="sessions")

    def __repr__(self):
        return f"<AgentSessionLink agent={self.agent_id} session={self.session_id}>"


class ScreenShareSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "screen_share_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    host_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    stream_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recording_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    def __repr__(self):
        return f"<ScreenShareSession session={self.session_id}>"


class DocumentCollaboration(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_collaborations"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<DocumentCollaboration {self.title}>"

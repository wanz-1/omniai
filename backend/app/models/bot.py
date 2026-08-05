import uuid
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import BotChannel
from app.models.base import Base, TimestampMixin, UUIDMixin


class Bot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bots"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    knowledge_base_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    channels: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deployment_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    widget_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("Project", back_populates="bots")
    conversations = relationship("BotConversation", back_populates="bot", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Bot(id={self.id}, name={self.name})"


class BotConversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bot_conversations"

    bot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), default=BotChannel.WEB, nullable=False)
    user_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    bot = relationship("Bot", back_populates="conversations")
    messages = relationship("BotMessage", back_populates="conversation", cascade="all, delete-orphan")


class BotMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bot_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bot_conversations.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    conversation = relationship("BotConversation", back_populates="messages")

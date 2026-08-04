import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PersonalAIAssistant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "personal_ai_assistants"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    personality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    preferences: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_interaction: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_interactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    memories = relationship("PersonalMemory", back_populates="assistant", cascade="all, delete-orphan")
    tasks = relationship("PersonalTask", back_populates="assistant", cascade="all, delete-orphan")
    knowledge_items = relationship("PersonalKnowledgeItem", back_populates="assistant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"PersonalAIAssistant(id={self.id}, name={self.name})"


class PersonalMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "personal_memories"

    assistant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("personal_ai_assistants.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    assistant = relationship("PersonalAIAssistant", back_populates="memories")

    def __repr__(self):
        return f"PersonalMemory(id={self.id}, title={self.title})"


class PersonalTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "personal_tasks"

    assistant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("personal_ai_assistants.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    assistant = relationship("PersonalAIAssistant", back_populates="tasks")

    def __repr__(self):
        return f"PersonalTask(id={self.id}, title={self.title})"


class PersonalKnowledgeItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "personal_knowledge_items"

    assistant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("personal_ai_assistants.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    assistant = relationship("PersonalAIAssistant", back_populates="knowledge_items")

    def __repr__(self):
        return f"PersonalKnowledgeItem(id={self.id}, title={self.title})"


class ExecutiveAssistant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "executive_assistants"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # ceo, cfo, cto, coo
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    insights: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    def __repr__(self):
        return f"ExecutiveAssistant(id={self.id}, role={self.role})"

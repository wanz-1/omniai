import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.core.constants import AgentStatus, AgentTaskStatus
from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_profiles"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AgentStatus.DRAFT, nullable=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    marketplace_listed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    skills = relationship("AgentSkill", back_populates="agent", cascade="all, delete-orphan")
    memories = relationship("AgentMemory", back_populates="agent", cascade="all, delete-orphan")
    tools = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"AgentProfile(id={self.id}, name={self.name}, role={self.role})"


class AgentSkill(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_skills"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proficiency: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )

    agent = relationship("AgentProfile", back_populates="skills")

    def __repr__(self):
        return f"AgentSkill(id={self.id}, name={self.name})"


class AgentMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_memories"

    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), default="fact", nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_organization: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    agent = relationship("AgentProfile", back_populates="memories")

    def __repr__(self):
        return f"AgentMemory(id={self.id}, key={self.key})"


class AgentTool(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_tools"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tool_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )

    agent = relationship("AgentProfile", back_populates="tools")

    def __repr__(self):
        return f"AgentTool(id={self.id}, name={self.name}, type={self.tool_type})"


class Workflow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trigger_event: Mapped[str | None] = mapped_column(String(100), nullable=True)
    trigger_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    agent = relationship("AgentProfile", back_populates="workflows")
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.order")

    def __repr__(self):
        return f"Workflow(id={self.id}, name={self.name})"


class WorkflowStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_steps"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True
    )

    workflow = relationship("Workflow", back_populates="steps")

    def __repr__(self):
        return f"WorkflowStep(id={self.id}, name={self.name}, type={self.step_type})"


class AgentTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_tasks"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=AgentTaskStatus.PENDING, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    execution_plan: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_tasks.id"), nullable=True, index=True
    )

    agent = relationship("AgentProfile")
    subtasks = relationship(
        "AgentTask",
        backref=backref("parent_task", remote_side="AgentTask.id"),
        foreign_keys="AgentTask.parent_task_id",
    )

    def __repr__(self):
        return f"AgentTask(id={self.id}, title={self.title}, status={self.status})"


class AgentExecution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_executions"

    status: Mapped[str] = mapped_column(String(20), default=AgentTaskStatus.PENDING, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    steps_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    steps_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input: Mapped[str | None] = mapped_column(Text, nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_log: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_tasks.id"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    agent = relationship("AgentProfile", back_populates="executions")

    def __repr__(self):
        return f"AgentExecution(id={self.id}, status={self.status})"


class AgentAnalytics(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_analytics"

    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_satisfaction: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_skills: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    daily_usage: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True, unique=True
    )

    agent = relationship("AgentProfile")

    def __repr__(self):
        return f"AgentAnalytics(id={self.id}, agent_id={self.agent_id})"

"""
Active AI Agent models – represents a running instance of an agent.

An ActiveAgent is a deployed, stateful runtime for an AgentProfile.
It can run in different modes:
- continuous: always-on loop checking for tasks
- on_demand: activated for a single task then idle
- scheduled: runs on cron schedule
- event_driven: reacts to webhooks / events
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ActiveAgentStatus(StrEnum):
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    WAITING_APPROVAL = "waiting_approval"


class ActiveAgentMode(StrEnum):
    CONTINUOUS = "continuous"
    ON_DEMAND = "on_demand"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    WEBHOOK = "webhook"


class ActiveAgent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "active_agents"

    # Identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    # Runtime state
    status: Mapped[str] = mapped_column(
        String(30), default=ActiveAgentStatus.IDLE, nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(
        String(30), default=ActiveAgentMode.CONTINUOUS, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Configuration overrides for this instance
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    # Heartbeat & lifecycle
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Current work
    current_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_tasks.id"), nullable=True, index=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tasks_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Scheduling
    cron_schedule: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "*/5 * * * *"
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent = relationship("AgentProfile", lazy="joined")
    current_task = relationship("AgentTask", foreign_keys=[current_task_id], lazy="joined")

    def __repr__(self) -> str:
        return f"ActiveAgent(id={self.id}, agent_id={self.agent_id}, status={self.status}, mode={self.mode})"


class ActiveAgentLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "active_agent_logs"

    active_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("active_agents.id"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    level: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info, warn, error, debug
    event_type: Mapped[str] = mapped_column(String(50), default="log", nullable=False)  # log, task_start, task_complete, tool_call, error, heartbeat
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self) -> str:
        return f"ActiveAgentLog(id={self.id}, active_agent_id={self.active_agent_id}, level={self.level})"


class ActiveAgentGoal(Base, UUIDMixin, TimestampMixin):
    """Long-term goal that an active agent works towards."""

    __tablename__ = "active_agent_goals"

    active_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("active_agents.id"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)  # active, completed, paused, archived
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    progress: Mapped[float] = mapped_column(default=0.0, nullable=False)  # 0.0 - 1.0

    # Success criteria / KPIs
    success_criteria: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"ActiveAgentGoal(id={self.id}, title={self.title}, progress={self.progress})"


class ActiveAgentMemory(Base, UUIDMixin, TimestampMixin):
    """Episodic / semantic memory specific to an active agent instance."""

    __tablename__ = "active_agent_memories"

    active_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("active_agents.id"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    key: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), default="episodic", nullable=False)  # episodic, semantic, procedural
    importance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # vector for similarity search
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"ActiveAgentMemory(id={self.id}, key={self.key}, type={self.memory_type})"

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentTeam(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_teams"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    members = relationship("AgentTeamMember", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("AgentTaskDelegation", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"AgentTeam(id={self.id}, name={self.name})"


class AgentTeamMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_team_members"

    role: Mapped[str] = mapped_column(String(100), nullable=False)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )

    team = relationship("AgentTeam", back_populates="members")
    agent = relationship("AgentProfile")

    def __repr__(self):
        return f"AgentTeamMember(team={self.team_id}, agent={self.agent_id}, role={self.role})"


class AgentMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_messages"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), default="direct", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="sent", nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_tasks.id"), nullable=True, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=True, index=True
    )

    sender = relationship("AgentProfile", foreign_keys=[sender_id])
    receiver = relationship("AgentProfile", foreign_keys=[receiver_id])

    def __repr__(self):
        return f"AgentMessage(id={self.id}, type={self.message_type})"


class AgentTaskDelegation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_task_delegations"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    input_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=True, index=True
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_task_delegations.id"), nullable=True, index=True
    )

    team = relationship("AgentTeam", back_populates="tasks")
    subtasks = relationship(
        "AgentTaskDelegation",
        backref=backref("parent_task", remote_side="AgentTaskDelegation.id"),
        foreign_keys="AgentTaskDelegation.parent_task_id",
    )

    def __repr__(self):
        return f"AgentTaskDelegation(id={self.id}, title={self.title}, status={self.status})"


class AgentReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_reviews"

    score: Mapped[float] = mapped_column(Float, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_type: Mapped[str] = mapped_column(String(50), default="peer", nullable=False)
    criteria_scores: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    suggestions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    reviewee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_task_delegations.id"), nullable=True, index=True
    )

    def __repr__(self):
        return f"AgentReview(id={self.id}, score={self.score}, type={self.review_type})"


class AgentMemoryNetwork(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_memory_network"

    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), default="fact", nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), default="team", nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=True, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    def __repr__(self):
        return f"AgentMemoryNetwork(id={self.id}, key={self.key})"


class AgentPermission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_permissions"

    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    access_level: Mapped[str] = mapped_column(String(20), default="allow", nullable=False)
    conditions: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=True, index=True
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    def __repr__(self):
        return f"AgentPermission(id={self.id}, agent={self.agent_id}, resource={self.resource}, action={self.action})"


class AgentPerformance(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_performance"

    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    daily_metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    review_scores: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True, unique=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=True, index=True
    )

    def __repr__(self):
        return f"AgentPerformance(id={self.id}, agent_id={self.agent_id})"


class AutonomousResearch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "autonomous_research"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    depth: Mapped[str] = mapped_column(String(20), default="standard", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    sources: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    findings: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    search_queries: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    def __repr__(self):
        return f"AutonomousResearch(id={self.id}, title={self.title})"


class DevProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dev_projects"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planning", nullable=False)
    requirements: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    architecture: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    generated_code: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    test_results: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    security_review: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    deployment_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_teams.id"), nullable=True, index=True
    )

    def __repr__(self):
        return f"DevProject(id={self.id}, name={self.name})"

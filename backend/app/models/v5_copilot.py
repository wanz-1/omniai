import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class CopilotConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "copilot_configs"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    knowledge_sources: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    available_tools: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    workflows: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    compliance_rules: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    organization = relationship("Organization")
    sessions = relationship("CopilotSession", back_populates="copilot", cascade="all, delete-orphan")
    workflows = relationship("CopilotWorkflow", back_populates="copilot", cascade="all, delete-orphan")
    analytics = relationship("CopilotAnalytic", back_populates="copilot", cascade="all, delete-orphan")
    knowledge_links = relationship("CopilotKnowledgeLink", back_populates="copilot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"CopilotConfig(id={self.id}, name={self.name}, industry={self.industry})"


class CopilotSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "copilot_sessions"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    copilot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_configs.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    copilot = relationship("CopilotConfig", back_populates="sessions")
    messages = relationship("CopilotMessage", back_populates="session", cascade="all, delete-orphan")
    recommendations = relationship("CopilotRecommendation", back_populates="session", cascade="all, delete-orphan")
    approvals = relationship("CopilotApproval", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"CopilotSession(id={self.id}, title={self.title}, status={self.status})"


class CopilotMessage(Base, UUIDMixin):
    __tablename__ = "copilot_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    tool_results: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session = relationship("CopilotSession", back_populates="messages")

    def __repr__(self):
        return f"CopilotMessage(id={self.id}, session_id={self.session_id}, role={self.role})"


class CopilotWorkflow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "copilot_workflows"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    copilot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_configs.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False)
    steps: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    triggers: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    copilot = relationship("CopilotConfig", back_populates="workflows")
    executions = relationship("CopilotWorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"CopilotWorkflow(id={self.id}, name={self.name}, type={self.workflow_type})"


class CopilotWorkflowExecution(Base, UUIDMixin):
    __tablename__ = "copilot_workflow_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_workflows.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    input_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow = relationship("CopilotWorkflow", back_populates="executions")

    def __repr__(self):
        return f"CopilotWorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})"


class CopilotRecommendation(Base, UUIDMixin):
    __tablename__ = "copilot_recommendations"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_sessions.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(50), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session = relationship("CopilotSession", back_populates="recommendations")

    def __repr__(self):
        return f"CopilotRecommendation(id={self.id}, type={self.recommendation_type}, title={self.title})"


class CopilotApproval(Base, UUIDMixin):
    __tablename__ = "copilot_approvals"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_sessions.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session = relationship("CopilotSession", back_populates="approvals")

    def __repr__(self):
        return f"CopilotApproval(id={self.id}, type={self.request_type}, status={self.status})"


class CopilotAnalytic(Base, UUIDMixin):
    __tablename__ = "copilot_analytics"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    copilot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_configs.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    copilot = relationship("CopilotConfig", back_populates="analytics")

    def __repr__(self):
        return f"CopilotAnalytic(id={self.id}, event_type={self.event_type})"


class CopilotDomainRule(Base, UUIDMixin):
    __tablename__ = "copilot_domain_rules"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    actions: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"CopilotDomainRule(id={self.id}, name={self.name}, severity={self.severity})"


class CopilotKnowledgeLink(Base, UUIDMixin):
    __tablename__ = "copilot_knowledge_links"

    copilot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("copilot_configs.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    connector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    copilot = relationship("CopilotConfig", back_populates="knowledge_links")

    def __repr__(self):
        return f"CopilotKnowledgeLink(id={self.id}, copilot_id={self.copilot_id})"

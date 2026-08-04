import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class KnowledgeConnector(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_connectors"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    credentials: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_frequency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sources = relationship("KnowledgeSource", back_populates="connector", cascade="all, delete-orphan")

    def __repr__(self):
        return f"KnowledgeConnector(id={self.id}, name={self.name}, type={self.connector_type})"


class KnowledgeSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_sources_v4"

    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_connectors.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    connector = relationship("KnowledgeConnector", back_populates="sources")
    documents = relationship("EnterpriseDocument", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"KnowledgeSource(id={self.id}, name={self.name}, type={self.source_type})"


class EnterpriseDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "enterprise_documents"

    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_sources_v4.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source = relationship("KnowledgeSource", back_populates="documents")

    def __repr__(self):
        return f"EnterpriseDocument(id={self.id}, title={self.title})"


class AIPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_policies"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rules: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    scope: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    def __repr__(self):
        return f"AIPolicy(id={self.id}, name={self.name}, type={self.policy_type})"


class AgentApprovalRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_approval_requests"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_profiles.id"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    capabilities: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"AgentApprovalRequest(id={self.id}, agent_name={self.agent_name}, status={self.status})"


class AIAuditEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_audit_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self):
        return f"AIAuditEvent(id={self.id}, event_type={self.event_type}, action={self.action})"


class AIMonitoringEventV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_monitoring_events_v4"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    model_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"AIMonitoringEventV4(id={self.id}, event_type={self.event_type}, status={self.status})"


class ObservabilityDashboard(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "observability_dashboards"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dashboard_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    def __repr__(self):
        return f"ObservabilityDashboard(id={self.id}, name={self.name}, type={self.dashboard_type})"


class EnterpriseAnalyticsV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "enterprise_analytics_v4"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    metric_category: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dimensions: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self):
        return f"EnterpriseAnalyticsV4(id={self.id}, name={self.metric_name}, value={self.metric_value})"


class AdoptionMetricV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "adoption_metrics_v4"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    feature_name: Mapped[str] = mapped_column(String(200), nullable=False)
    total_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    adoption_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"AdoptionMetricV4(id={self.id}, feature={self.feature_name}, rate={self.adoption_rate})"


class CostSavingsRecordV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cost_savings_v4"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_saved: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"CostSavingsRecordV4(id={self.id}, category={self.category}, saved={self.amount_saved})"

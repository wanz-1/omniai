import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class InfrastructureRegion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "infrastructure_regions"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    clusters = relationship("ClusterDeployment", back_populates="region", cascade="all, delete-orphan")

    def __repr__(self):
        return f"InfrastructureRegion(id={self.id}, name={self.name})"


class ClusterDeployment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cluster_deployments"

    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("infrastructure_regions.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cluster_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="provisioning", nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    endpoints: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    health_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    region = relationship("InfrastructureRegion", back_populates="clusters")
    deployments = relationship("ServiceDeployment", back_populates="cluster", cascade="all, delete-orphan")

    def __repr__(self):
        return f"ClusterDeployment(id={self.id}, name={self.name})"


class ServiceDeployment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "service_deployments"

    cluster_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cluster_deployments.id"), nullable=False, index=True)
    service_name: Mapped[str] = mapped_column(String(200), nullable=False)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="deploying", nullable=False)
    replicas: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    target_replicas: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    resources: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    endpoints: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    cluster = relationship("ClusterDeployment", back_populates="deployments")

    def __repr__(self):
        return f"ServiceDeployment(id={self.id}, service_name={self.service_name})"


class AIModelRegistry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_model_registry"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    cost_per_token: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_p50: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_p99: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    routing_rules: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    supported_regions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    def __repr__(self):
        return f"AIModelRegistry(id={self.id}, name={self.name})"


class SecurityEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "security_events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"SecurityEvent(id={self.id}, event_type={self.event_type})"


class MonitoringMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "monitoring_metrics"

    metric_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("infrastructure_regions.id"), nullable=True, index=True)
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cluster_deployments.id"), nullable=True, index=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BackupRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "backup_records"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    backup_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self):
        return f"BackupRecord(id={self.id}, name={self.name})"


class ComplianceReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_reports"

    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("infrastructure_regions.id"), nullable=True, index=True)
    data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    findings: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"ComplianceReport(id={self.id}, title={self.title})"


class OrganizationPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organization_policies"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    policy_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    auto_remediate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"OrganizationPolicy(id={self.id}, name={self.name})"


class DataResidencyConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_residency_configs"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("infrastructure_regions.id"), nullable=False, index=True)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, default=365, nullable=False)
    encryption_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    encryption_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    allow_export: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_processing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)


class DeveloperApiKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "developer_api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    scopes: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

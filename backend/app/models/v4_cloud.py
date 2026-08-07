import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TenantEnvironment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tenant_environments"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    environment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="provisioning", nullable=False)
    is_ha: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scaling_policy: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    backup_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    dr_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"TenantEnvironment(id={self.id}, name={self.name})"


class RegionalDeployment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "regional_deployments"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant_environments.id"), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="deploying", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    endpoint_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    health_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self):
        return f"RegionalDeployment(id={self.id}, region={self.region})"


class BackupRecordV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "backup_records_v4"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant_environments.id"), nullable=False, index=True)
    backup_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    size_bytes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self):
        return f"BackupRecordV4(id={self.id}, backup_type={self.backup_type})"


class DisasterRecoveryPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "disaster_recovery_plans"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant_environments.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rpo_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    rto_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    regions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    steps: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"DisasterRecoveryPlan(id={self.id}, name={self.name})"


class UsageMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "usage_metrics_v4"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenant_environments.id"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dimensions: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    def __repr__(self):
        return f"UsageMetric(id={self.id}, metric_name={self.metric_name})"


class AppCategory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "app_categories"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(200), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"AppCategory(id={self.id}, name={self.name})"


class AppListing(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "app_listings"

    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_categories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    publisher: Mapped[str] = mapped_column(String(200), nullable=False)
    publisher_website: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshots: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    features: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    pricing_model: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    documentation_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_schema: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    total_installs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    def __repr__(self):
        return f"AppListing(id={self.id}, name={self.name})"


class AppInstallation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "app_installations"

    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_listings.id"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="installed", nullable=False)
    installed_version: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    customizations: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    app = relationship("AppListing")

    def __repr__(self):
        return f"AppInstallation(id={self.id}, app_id={self.app_id})"


class AppPurchase(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "app_purchases"

    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_listings.id"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    purchase_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    license_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    app = relationship("AppListing")

    def __repr__(self):
        return f"AppPurchase(id={self.id}, app_id={self.app_id})"


class AppReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "app_reviews_v4"

    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_listings.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    app = relationship("AppListing")

    def __repr__(self):
        return f"AppReview(id={self.id}, app_id={self.app_id})"


class WorkflowTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_templates_v4"

    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    steps: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    ai_agents: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    forms: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    approval_rules: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    reports: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    dashboards: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    total_installs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self):
        return f"WorkflowTemplate(id={self.id}, name={self.name})"


class WorkflowInstallationV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_installations_v4"

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_templates_v4.id"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="installed", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    customizations: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"WorkflowInstallationV4(id={self.id}, template_id={self.template_id})"


class WorkflowRatingV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_ratings_v4"

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_templates_v4.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"WorkflowRatingV4(id={self.id}, template_id={self.template_id})"

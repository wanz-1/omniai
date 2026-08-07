import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ConnectorDefinition(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "connector_definitions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    auth_type: Mapped[str] = mapped_column(String(30), nullable=False)
    config_schema: Mapped[dict] = mapped_column(JSONB, default=dict)
    permissions: Mapped[list] = mapped_column(JSONB, default=list)
    actions: Mapped[list] = mapped_column(JSONB, default=list)
    events: Mapped[list] = mapped_column(JSONB, default=list)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    integrations = relationship("ConnectorIntegration", back_populates="connector")

    def __repr__(self):
        return f"<ConnectorDefinition {self.name} ({self.connector_type})>"


class ConnectorIntegration(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "connector_integrations"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_definitions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="disconnected")
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    connector = relationship("ConnectorDefinition", back_populates="integrations")
    credentials = relationship("ConnectorCredential", back_populates="integration", cascade="all, delete-orphan")
    sync_jobs = relationship("SyncJob", back_populates="integration", cascade="all, delete-orphan")
    permissions = relationship("ConnectorPermission", back_populates="integration", cascade="all, delete-orphan")
    logs = relationship("ConnectorLog", back_populates="integration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ConnectorIntegration {self.name} ({self.status})>"


class ConnectorCredential(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "connector_credentials"

    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_integrations.id"), nullable=False, index=True)
    credential_type: Mapped[str] = mapped_column(String(30), nullable=False)
    encrypted_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    integration = relationship("ConnectorIntegration", back_populates="credentials")

    def __repr__(self):
        return f"<ConnectorCredential {self.credential_type}>"


class ConnectorPermission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "connector_permissions"

    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_integrations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    principal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    principal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    permission: Mapped[str] = mapped_column(String(50), nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    integration = relationship("ConnectorIntegration", back_populates="permissions")

    def __repr__(self):
        return f"<ConnectorPermission {self.permission} ({self.principal_type})>"


class SyncJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sync_jobs"

    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_integrations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    items_processed: Mapped[int] = mapped_column(Integer, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, default=0)
    items_created: Mapped[int] = mapped_column(Integer, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, default=0)
    items_deleted: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[list] = mapped_column(JSONB, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    integration = relationship("ConnectorIntegration", back_populates="sync_jobs")

    def __repr__(self):
        return f"<SyncJob {self.sync_type} ({self.status})>"


class WebhookEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "webhook_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    integration_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_integrations.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="received")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<WebhookEvent {self.event_type} ({self.status})>"


class ConnectorLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "connector_logs"

    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_integrations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    integration = relationship("ConnectorIntegration", back_populates="logs")

    def __repr__(self):
        return f"<ConnectorLog {self.action} ({self.level})>"


class ConnectorApiKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "connector_api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    scopes: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    def __repr__(self):
        return f"<ConnectorApiKey {self.name} ({self.key_prefix}...)>"


class MarketplaceConnector(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketplace_connectors"

    connector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_definitions.id"), nullable=False)
    publisher_org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    reviews: Mapped[list] = mapped_column(JSONB, default=list)
    pricing_tier: Mapped[str] = mapped_column(String(20), default="free")
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    documentation: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self):
        return f"<MarketplaceConnector rating={self.rating} downloads={self.download_count}>"


class CustomConnectorEndpoint(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "custom_connector_endpoints"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_type: Mapped[str] = mapped_column(String(20), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_method: Mapped[str] = mapped_column(String(30), nullable=False)
    headers: Mapped[dict] = mapped_column(JSONB, default=dict)
    endpoints: Mapped[list] = mapped_column(JSONB, default=list)
    rate_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self):
        return f"<CustomConnectorEndpoint {self.name} ({self.api_type})>"

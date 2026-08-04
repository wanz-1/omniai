import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class EnterpriseIntegrationV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "enterprise_integrations_v4"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    integration_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    credentials: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_frequency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    auth_records = relationship("IntegrationAuthV4", back_populates="integration", cascade="all, delete-orphan")
    sync_records = relationship("SyncRecordV4", back_populates="integration", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"EnterpriseIntegrationV4(id={self.id}, name={self.name}, integration_type={self.integration_type})"


class IntegrationAuthV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "integration_auth_v4"

    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enterprise_integrations_v4.id"), nullable=False, index=True)
    auth_type: Mapped[str] = mapped_column(String(20), nullable=False)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    integration = relationship("EnterpriseIntegrationV4", back_populates="auth_records")

    def __repr__(self) -> str:
        return f"IntegrationAuthV4(id={self.id}, auth_type={self.auth_type})"


class SyncRecordV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sync_records_v4"

    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enterprise_integrations_v4.id"), nullable=False, index=True)
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_log: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    integration = relationship("EnterpriseIntegrationV4", back_populates="sync_records")

    def __repr__(self) -> str:
        return f"SyncRecordV4(id={self.id}, sync_type={self.sync_type}, status={self.status})"


class AIAppDefinition(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_app_definitions"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    natural_language_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    components: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    data_model: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    ai_actions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    workflows: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    api_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    ui_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    components_list = relationship("AppComponentV4", back_populates="app", cascade="all, delete-orphan")
    published_instances = relationship("PublishedAppV4", back_populates="app", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"AIAppDefinition(id={self.id}, name={self.name}, status={self.status})"


class AppComponentV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "app_components_v4"

    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_app_definitions.id"), nullable=False, index=True)
    component_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    position: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    app = relationship("AIAppDefinition", back_populates="components_list")

    def __repr__(self) -> str:
        return f"AppComponentV4(id={self.id}, component_type={self.component_type}, name={self.name})"


class PublishedAppV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "published_apps_v4"

    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_app_definitions.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    published_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    api_endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deployed_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    analytics: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    app = relationship("AIAppDefinition", back_populates="published_instances")

    def __repr__(self) -> str:
        return f"PublishedAppV4(id={self.id}, status={self.status})"


class ModelRegistryEntryV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "model_registry_v4"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    model_provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model_version: Mapped[str] = mapped_column(String(30), nullable=False)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    cost_per_input_token: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_per_output_token: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_p50_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_p99_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fallback_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    benchmarks = relationship("ModelBenchmarkV4", back_populates="model", cascade="all, delete-orphan")
    fine_tuned_models = relationship("FineTunedModelV4", back_populates="base_model", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"ModelRegistryEntryV4(id={self.id}, model_name={self.model_name}, model_provider={self.model_provider})"


class ModelBenchmarkV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "model_benchmarks_v4"

    model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_registry_v4.id"), nullable=False, index=True)
    benchmark_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    test_dataset: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    model = relationship("ModelRegistryEntryV4", back_populates="benchmarks")

    def __repr__(self) -> str:
        return f"ModelBenchmarkV4(id={self.id}, benchmark_name={self.benchmark_name}, score={self.score})"


class FineTunedModelV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fine_tuned_models_v4"

    base_model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_registry_v4.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_data_config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    hyperparameters: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    model_endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_multiplier: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    base_model = relationship("ModelRegistryEntryV4", back_populates="fine_tuned_models")

    def __repr__(self) -> str:
        return f"FineTunedModelV4(id={self.id}, name={self.name}, status={self.status})"


class SdkReleaseV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sdk_releases_v4"

    sdk_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sdk_language: Mapped[str] = mapped_column(String(30), nullable=False)
    sdk_version: Mapped[str] = mapped_column(String(20), nullable=False)
    release_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    breaking_changes: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    def __repr__(self) -> str:
        return f"SdkReleaseV4(id={self.id}, sdk_name={self.sdk_name}, sdk_version={self.sdk_version})"


class PluginDefinitionV4(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plugin_definitions_v4"

    publisher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plugin_type: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    config_schema: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    hooks: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    permissions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"PluginDefinitionV4(id={self.id}, name={self.name}, plugin_type={self.plugin_type})"

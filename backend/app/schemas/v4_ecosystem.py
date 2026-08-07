import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnterpriseIntegrationV4Response(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    integration_type: str
    config: dict | None = None
    status: str
    last_sync_at: datetime | None = None
    is_active: bool = True
    webhook_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


class IntegrationAuthV4Response(BaseModel):
    id: uuid.UUID
    integration_id: uuid.UUID
    auth_type: str
    is_valid: bool = True
    scopes: list | None = None
    token_expires_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class SyncRecordV4Response(BaseModel):
    id: uuid.UUID
    integration_id: uuid.UUID
    sync_type: str
    status: str
    records_processed: int = 0
    records_failed: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class AIAppDefinitionResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None = None
    natural_language_prompt: str | None = None
    status: str
    components: list | None = None
    data_model: dict | None = None
    ai_actions: list | None = None
    workflows: list | None = None
    api_config: dict | None = None
    ui_config: dict | None = None
    version: str
    is_published: bool = False
    published_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


class AIAppGenerateResponse(BaseModel):
    app: AIAppDefinitionResponse
    suggestion: str


class AppComponentV4Response(BaseModel):
    id: uuid.UUID
    app_id: uuid.UUID
    component_type: str
    name: str
    config: dict | None = None
    is_visible: bool = True
    model_config = ConfigDict(from_attributes=True)


class PublishedAppV4Response(BaseModel):
    id: uuid.UUID
    app_id: uuid.UUID
    organization_id: uuid.UUID
    published_url: str
    api_endpoint: str | None = None
    deployed_version: str
    deployed_at: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)


class ModelRegistryEntryV4Response(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    model_name: str
    model_provider: str
    model_version: str
    capabilities: list | None = None
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    latency_p50_ms: float = 0.0
    is_active: bool = True
    fallback_priority: int = 0
    is_default: bool = False
    model_config = ConfigDict(from_attributes=True)


class ModelBenchmarkV4Response(BaseModel):
    id: uuid.UUID
    model_id: uuid.UUID
    benchmark_name: str
    score: float
    metric_name: str
    tested_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FineTunedModelV4Response(BaseModel):
    id: uuid.UUID
    base_model_id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    status: str
    model_endpoint: str | None = None
    accuracy: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class SdkReleaseV4Response(BaseModel):
    id: uuid.UUID
    sdk_name: str
    sdk_language: str
    sdk_version: str
    release_notes: str | None = None
    documentation_url: str | None = None
    download_url: str
    is_latest: bool = False
    published_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PluginDefinitionV4Response(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    plugin_type: str
    version: str
    config_schema: dict | None = None
    is_verified: bool = False
    is_active: bool = True
    download_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class SyncRequest(BaseModel):
    integration_id: uuid.UUID
    sync_type: str
    full: bool = False


class SyncResponse(BaseModel):
    sync_id: str
    status: str
    records_processed: int
    message: str

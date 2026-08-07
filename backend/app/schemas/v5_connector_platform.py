import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConnectorDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    connector_type: str
    category: str
    description: str | None
    icon_url: str | None
    version: str
    auth_type: str
    config_schema: dict
    permissions: list
    actions: list
    events: list
    is_official: bool
    is_active: bool
    documentation_url: str | None
    publisher: str | None
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class ConnectorIntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    connector_id: uuid.UUID
    name: str
    status: str
    config: dict
    settings: dict
    is_active: bool
    last_sync_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ConnectorCredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    integration_id: uuid.UUID
    credential_type: str
    expires_at: datetime | None
    is_expired: bool
    rotated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ConnectorPermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    integration_id: uuid.UUID
    organization_id: uuid.UUID
    principal_type: str
    principal_id: uuid.UUID
    permission: str
    granted_by: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SyncJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    integration_id: uuid.UUID
    organization_id: uuid.UUID
    sync_type: str
    status: str
    items_total: int
    items_processed: int
    items_failed: int
    items_created: int
    items_updated: int
    items_deleted: int
    error_log: list
    started_at: datetime | None
    completed_at: datetime | None
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class WebhookEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    integration_id: uuid.UUID | None
    event_type: str
    source: str
    payload: dict
    status: str
    processed_at: datetime | None
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class ConnectorLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    integration_id: uuid.UUID
    organization_id: uuid.UUID
    level: str
    action: str
    message: str | None
    details: dict | None
    ip_address: str | None
    created_at: datetime
    updated_at: datetime


class ConnectorApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    key_prefix: str
    scopes: list
    status: str
    expires_at: datetime | None
    last_used_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MarketplaceConnectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    connector_id: uuid.UUID
    publisher_org_id: uuid.UUID | None
    is_verified: bool
    rating: float
    download_count: int
    reviews: list
    pricing_tier: str
    price: float | None
    documentation: str | None
    support_url: str | None
    created_at: datetime
    updated_at: datetime


class CustomConnectorEndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    api_type: str
    base_url: str
    auth_method: str
    headers: dict
    endpoints: list
    rate_limit: int | None
    is_active: bool
    created_by: uuid.UUID
    meta_data: dict | None
    created_at: datetime
    updated_at: datetime


class InstallConnectorRequest(BaseModel):
    connector_id: uuid.UUID
    name: str
    config: dict | None
    credentials: dict | None


class CreateCustomConnectorRequest(BaseModel):
    name: str
    api_type: str
    base_url: str
    auth_method: str
    headers: dict | None
    endpoints: list | None
    rate_limit: int | None


class AuthenticateConnectorRequest(BaseModel):
    integration_id: uuid.UUID
    auth_data: dict


class SyncConnectorRequest(BaseModel):
    integration_id: uuid.UUID
    sync_type: str


class RegisterWebhookRequest(BaseModel):
    integration_id: uuid.UUID
    event_type: str
    target_url: str
    secret: str | None


class CreateApiKeyRequest(BaseModel):
    name: str
    scopes: list | None
    expires_at: str | None


class ConnectorQueryRequest(BaseModel):
    integration_id: uuid.UUID
    action: str
    params: dict | None


class ConnectorDashboardResponse(BaseModel):
    total_connectors: int
    active_connectors: int
    total_syncs: int
    last_sync_at: datetime | None
    total_webhooks: int
    recent_webhooks: int
    total_errors: int
    by_category: dict

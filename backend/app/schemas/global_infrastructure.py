import uuid
from datetime import datetime
from pydantic import BaseModel


class RegionResponse(BaseModel):
    id: uuid.UUID; name: str; slug: str; description: str | None = None
    provider: str; location: str | None = None; status: str = "active"
    is_active: bool = True; priority: int = 0
    class Config: from_attributes = True


class ClusterResponse(BaseModel):
    id: uuid.UUID; region_id: uuid.UUID; name: str; cluster_type: str
    version: str; status: str; node_count: int = 1
    health_status: str = "unknown"
    class Config: from_attributes = True


class ServiceDeploymentResponse(BaseModel):
    id: uuid.UUID; cluster_id: uuid.UUID; service_name: str
    service_type: str; version: str; status: str
    replicas: int = 1; target_replicas: int = 1
    class Config: from_attributes = True


class ModelRegistryResponse(BaseModel):
    id: uuid.UUID; name: str; provider: str; model_id: str
    model_type: str; capabilities: list | None = None
    cost_per_token: float = 0.0; latency_p50: float = 0.0
    latency_p99: float = 0.0; max_tokens: int = 4096; is_active: bool = True
    class Config: from_attributes = True


class SecurityEventResponse(BaseModel):
    id: uuid.UUID; event_type: str; severity: str
    source: str | None = None; description: str | None = None
    is_resolved: bool = False; created_at: datetime | None = None
    class Config: from_attributes = True


class MonitoringMetricResponse(BaseModel):
    id: uuid.UUID; metric_name: str; metric_value: float
    metric_type: str; unit: str | None = None; source: str | None = None
    recorded_at: datetime
    class Config: from_attributes = True


class BackupRecordResponse(BaseModel):
    id: uuid.UUID; name: str; backup_type: str; target: str
    status: str; size_bytes: int | None = None; location: str | None = None
    started_at: datetime | None = None; completed_at: datetime | None = None
    class Config: from_attributes = True


class ComplianceReportResponse(BaseModel):
    id: uuid.UUID; report_type: str; title: str
    description: str | None = None; status: str = "draft"
    generated_at: datetime | None = None
    class Config: from_attributes = True


class OrganizationPolicyResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; policy_type: str
    name: str; description: str | None = None; is_active: bool = True
    severity: str = "medium"; auto_remediate: bool = False
    class Config: from_attributes = True


class DataResidencyResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; region_id: uuid.UUID
    data_type: str; retention_days: int = 365
    encryption_enabled: bool = True; is_active: bool = True
    class Config: from_attributes = True


class DeveloperApiKeyResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; name: str
    key_prefix: str; scopes: list | None = None
    rate_limit: int = 1000; is_active: bool = True
    expires_at: datetime | None = None; created_at: datetime | None = None
    class Config: from_attributes = True


class DeveloperApiKeyCreate(BaseModel):
    name: str; scopes: list[str] | None = None
    rate_limit: int = 1000; expires_at: datetime | None = None


class ModelRouteRequest(BaseModel):
    task: str; complexity: str = "medium"; max_cost: float | None = None
    preferred_provider: str | None = None; required_capabilities: list[str] | None = None


class ModelRouteResponse(BaseModel):
    model_id: str; provider: str; name: str; cost: float; latency: float; reason: str


class AlertRule(BaseModel):
    metric: str; operator: str; threshold: float; duration: str; channels: list[str]

import uuid
from datetime import datetime
from pydantic import BaseModel


class TenantEnvironmentResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; name: str; environment_type: str
    region: str; config: dict | None = None; status: str; is_ha: bool = False
    scaling_policy: dict | None = None; backup_config: dict | None = None
    dr_config: dict | None = None; is_active: bool = True
    class Config: from_attributes = True


class RegionalDeploymentResponse(BaseModel):
    id: uuid.UUID; tenant_id: uuid.UUID; region: str; status: str
    config: dict | None = None; endpoint_url: str | None = None
    deployed_at: datetime | None = None; health_status: str | None = None
    metrics: dict | None = None
    class Config: from_attributes = True


class BackupRecordV4Response(BaseModel):
    id: uuid.UUID; tenant_id: uuid.UUID; backup_type: str; status: str
    size_bytes: int = 0; location: str | None = None
    started_at: datetime | None = None; completed_at: datetime | None = None
    class Config: from_attributes = True


class DisasterRecoveryPlanResponse(BaseModel):
    id: uuid.UUID; tenant_id: uuid.UUID; name: str
    rpo_minutes: int; rto_minutes: int; regions: list | None = None
    status: str; is_active: bool = True
    class Config: from_attributes = True


class UsageMetricResponse(BaseModel):
    id: uuid.UUID; tenant_id: uuid.UUID; metric_name: str
    metric_value: float; unit: str | None = None
    recorded_at: datetime; dimensions: dict | None = None
    class Config: from_attributes = True


class AppCategoryResponse(BaseModel):
    id: uuid.UUID; name: str; slug: str; description: str | None = None
    icon: str | None = None; display_order: int = 0; is_active: bool = True
    class Config: from_attributes = True


class AppListingResponse(BaseModel):
    id: uuid.UUID; category_id: uuid.UUID; name: str; slug: str
    description: str | None = None; short_description: str | None = None
    publisher: str; pricing_model: str; price: float = 0.0
    currency: str = "USD"; is_verified: bool = False; is_active: bool = True
    version: str; total_installs: int = 0; avg_rating: float = 0.0
    tags: list | None = None; features: list | None = None
    screenshots: list | None = None
    class Config: from_attributes = True


class AppInstallationResponse(BaseModel):
    id: uuid.UUID; app_id: uuid.UUID; tenant_id: uuid.UUID
    organization_id: uuid.UUID; status: str
    installed_version: str; config: dict | None = None
    customizations: dict | None = None; installed_at: datetime
    last_used_at: datetime | None = None; is_active: bool = True
    class Config: from_attributes = True


class AppPurchaseResponse(BaseModel):
    id: uuid.UUID; app_id: uuid.UUID; tenant_id: uuid.UUID
    organization_id: uuid.UUID; purchase_type: str; amount: float
    currency: str; status: str; license_key: str | None = None
    purchased_at: datetime; expires_at: datetime | None = None
    class Config: from_attributes = True


class AppReviewV4Response(BaseModel):
    id: uuid.UUID; app_id: uuid.UUID; user_id: uuid.UUID; rating: float
    review_text: str | None = None; is_verified_purchase: bool = False
    created_at: datetime
    class Config: from_attributes = True


class WorkflowTemplateResponse(BaseModel):
    id: uuid.UUID; name: str; slug: str; description: str | None = None
    category: str | None = None; industry: str | None = None
    steps: list | None = None; ai_agents: list | None = None
    forms: list | None = None; approval_rules: list | None = None
    reports: list | None = None; dashboards: list | None = None
    tags: list | None = None; is_verified: bool = False; is_active: bool = True
    version: str; total_installs: int = 0; avg_rating: float = 0.0
    class Config: from_attributes = True


class WorkflowInstallationV4Response(BaseModel):
    id: uuid.UUID; template_id: uuid.UUID; tenant_id: uuid.UUID
    organization_id: uuid.UUID; status: str; config: dict | None = None
    customizations: dict | None = None; installed_at: datetime
    execution_count: int = 0; is_active: bool = True
    class Config: from_attributes = True


class WorkflowRatingV4Response(BaseModel):
    id: uuid.UUID; template_id: uuid.UUID; user_id: uuid.UUID; rating: float
    review_text: str | None = None
    class Config: from_attributes = True


class AppQueryRequest(BaseModel):
    query: str


class AppQueryResponse(BaseModel):
    response: str; apps: list; total: int

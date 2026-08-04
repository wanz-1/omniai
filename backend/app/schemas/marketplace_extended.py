import uuid
from datetime import datetime
from pydantic import BaseModel


class ProductCategoryResponse(BaseModel):
    id: uuid.UUID; name: str; slug: str; description: str | None = None
    icon: str | None = None; parent_id: uuid.UUID | None = None; sort_order: int = 0
    is_active: bool; subcategories: list | None = None
    class Config: from_attributes = True


class ProductVersionResponse(BaseModel):
    id: uuid.UUID; version: str; changelog: str | None = None
    release_notes: str | None = None; file_size: int = 0; is_deprecated: bool = False
    class Config: from_attributes = True


class ProductReviewCreate(BaseModel):
    product_id: uuid.UUID; rating: int; title: str | None = None
    content: str | None = None; pros: list[str] | None = None; cons: list[str] | None = None


class ProductReviewResponse(BaseModel):
    id: uuid.UUID; product_id: uuid.UUID; user_id: uuid.UUID
    rating: int; title: str | None = None; content: str | None = None
    pros: list | None = None; cons: list | None = None; is_verified_purchase: bool = False
    created_at: datetime | None = None
    class Config: from_attributes = True


class CreatorProfileResponse(BaseModel):
    id: uuid.UUID; display_name: str; bio: str | None = None
    avatar_url: str | None = None; website: str | None = None; company: str | None = None
    is_verified: bool; total_sales: int; total_revenue: float; total_products: int
    average_rating: float | None = None; skills: list | None = None
    class Config: from_attributes = True


class PluginDefinitionResponse(BaseModel):
    id: uuid.UUID; name: str; slug: str; description: str | None = None
    plugin_type: str; version: str; is_active: bool; is_official: bool
    config_schema: dict | None = None; permissions_required: list | None = None
    source_url: str | None = None; documentation_url: str | None = None; author_id: uuid.UUID
    class Config: from_attributes = True


class PluginInstallResponse(BaseModel):
    id: uuid.UUID; plugin_id: uuid.UUID; config: dict | None = None
    is_enabled: bool; installed_version: str
    class Config: from_attributes = True


class VerificationResponse(BaseModel):
    id: uuid.UUID; level: str; status: str; score: float | None = None
    security_score: float | None = None; performance_score: float | None = None
    quality_score: float | None = None; documentation_score: float | None = None
    issues: list | None = None; report: str | None = None
    class Config: from_attributes = True


class PublishRequest(BaseModel):
    name: str; description: str; short_description: str | None = None
    item_type: str; category: str | None = None; price: float = 0.0
    tags: list[str] | None = None; preview_image_url: str | None = None
    demo_url: str | None = None; config: dict | None = None
    source_type: str | None = None; source_id: uuid.UUID | None = None


class EnterpriseListingCreate(BaseModel):
    product_id: uuid.UUID; is_private: bool = False
    allowed_orgs: list[uuid.UUID] | None = None; license_type: str = "enterprise"
    custom_price: float | None = None; support_level: str = "standard"


class CreatorDashboardResponse(BaseModel):
    total_products: int; total_sales: int; total_revenue: float
    average_rating: float | None = None; recent_sales: list = []
    products: list = []; analytics: dict = {}
    class Config: from_attributes = True


class SDKGenerateRequest(BaseModel):
    language: str = "python"; features: list[str] | None = None
    organization_id: uuid.UUID | None = None

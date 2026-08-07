import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import WebsiteFramework, WebsiteStyling


class WebsiteCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    project_id: uuid.UUID | None = None
    template_id: str | None = None
    framework: WebsiteFramework = WebsiteFramework.HTML_CSS
    styling: WebsiteStyling = WebsiteStyling.TAILWIND


class WebsiteGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=5000)
    pages: list[dict] | None = None


class WebsiteCustomizeRequest(BaseModel):
    theme_config: dict | None = None
    pages: list[dict] | None = None


class WebsitePublishRequest(BaseModel):
    custom_domain: str | None = None
    subdomain: str | None = None


class WebsiteDeployRequest(BaseModel):
    platform: str = Field(default="vercel", pattern="^(vercel|netlify|self-hosted)$")


class WebsiteResponse(BaseModel):
    id: uuid.UUID
    name: str
    template_id: str | None = None
    framework: str
    styling: str
    pages: dict | None = None
    theme_config: dict | None = None
    preview_url: str | None = None
    published_url: str | None = None
    deployment_status: str
    custom_domain: str | None = None
    is_published: bool
    project_id: uuid.UUID | None = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebsiteUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    pages: list[dict] | None = None
    theme_config: dict | None = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    preview_url: str | None = None
    frameworks: list[str]


class BrandingRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    industry: str | None = None


class BrandingResponse(BaseModel):
    brand_names: list[str] = []
    taglines: list[str] = []
    color_palettes: list[dict] = []
    logo_concepts: list[str] = []
    business_descriptions: list[str] = []


class WebsiteExportRequest(BaseModel):
    include_assets: bool = True
    minify: bool = False

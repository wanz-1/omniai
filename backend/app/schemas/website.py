import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import WebsiteFramework, WebsiteStyling


class WebsiteCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    project_id: Optional[uuid.UUID] = None
    template_id: Optional[str] = None
    framework: WebsiteFramework = WebsiteFramework.HTML_CSS
    styling: WebsiteStyling = WebsiteStyling.TAILWIND


class WebsiteGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=5000)
    pages: Optional[list[dict]] = None


class WebsiteCustomizeRequest(BaseModel):
    theme_config: Optional[dict] = None
    pages: Optional[list[dict]] = None


class WebsitePublishRequest(BaseModel):
    custom_domain: Optional[str] = None
    subdomain: Optional[str] = None


class WebsiteDeployRequest(BaseModel):
    platform: str = Field(default="vercel", pattern="^(vercel|netlify|self-hosted)$")


class WebsiteResponse(BaseModel):
    id: uuid.UUID
    name: str
    template_id: Optional[str] = None
    framework: str
    styling: str
    pages: Optional[dict] = None
    theme_config: Optional[dict] = None
    preview_url: Optional[str] = None
    published_url: Optional[str] = None
    deployment_status: str
    custom_domain: Optional[str] = None
    is_published: bool
    project_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebsiteUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    pages: Optional[list[dict]] = None
    theme_config: Optional[dict] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    preview_url: Optional[str] = None
    frameworks: list[str]


class BrandingRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    industry: Optional[str] = None


class BrandingResponse(BaseModel):
    brand_names: list[str] = []
    taglines: list[str] = []
    color_palettes: list[dict] = []
    logo_concepts: list[str] = []
    business_descriptions: list[str] = []


class WebsiteExportRequest(BaseModel):
    include_assets: bool = True
    minify: bool = False

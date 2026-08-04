import uuid
from datetime import datetime
from pydantic import BaseModel


class StartupProjectResponse(BaseModel):
    id: uuid.UUID; name: str; description: str | None = None
    industry: str | None = None; status: str = "planning"
    class Config: from_attributes = True


class StartupGenerateRequest(BaseModel):
    name: str; description: str; industry: str | None = None
    features: list[str] | None = None; platform: str = "web"


class AIGeneratedProductResponse(BaseModel):
    id: uuid.UUID; startup_id: uuid.UUID; product_type: str; name: str
    description: str | None = None; platform: str | None = None; status: str = "generated"
    class Config: from_attributes = True


class ProductIdeaResponse(BaseModel):
    id: uuid.UUID; title: str; description: str | None = None
    industry: str | None = None; status: str = "draft"
    validation: dict | None = None; market_research: dict | None = None
    user_stories: list | None = None; feature_roadmap: list | None = None
    class Config: from_attributes = True


class DesignAssetResponse(BaseModel):
    id: uuid.UUID; name: str; asset_type: str; description: str | None = None
    style: str | None = None; is_favorite: bool = False
    class Config: from_attributes = True


class DesignGenerateRequest(BaseModel):
    name: str; asset_type: str; description: str; style: str | None = None
    prompt: str | None = None

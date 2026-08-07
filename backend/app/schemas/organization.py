import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    logo_url: str | None = None
    settings: dict | None = None


class OrganizationMemberAddRequest(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class OrganizationMemberResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    logo_url: str | None = None
    plan: str
    is_active: bool
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

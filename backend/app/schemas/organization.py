import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    logo_url: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationMemberAddRequest(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class OrganizationMemberResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    logo_url: Optional[str] = None
    plan: str
    is_active: bool
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

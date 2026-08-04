import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import ProjectType


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: ProjectType = ProjectType.GENERAL
    organization_id: Optional[uuid.UUID] = None


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_archived: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    type: str
    is_archived: bool
    user_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from pydantic import BaseModel


class VideoJobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    input_asset_id: uuid.UUID
    job_type: str
    status: str
    progress: float = 0
    output: dict | None = None
    error: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class VideoJobCreateResponse(BaseModel):
    job_id: uuid.UUID
    asset_id: uuid.UUID
    status: str
    job_type: str
    output: dict | None = None

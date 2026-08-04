import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalyzeImageResponse(BaseModel):
    description: str
    model: str = "gpt-4o"
    tokens: int = 0


class OCRResponse(BaseModel):
    raw_text: str | None = None
    structured_data: dict | None = None
    confidence: float | None = None
    model: str = "gpt-4o"
    tokens: int = 0


class DocumentAnalysisResponse(BaseModel):
    document_type: str = "unknown"
    language: str = "unknown"
    page_count: int | None = None
    key_fields: dict[str, Any] = Field(default_factory=dict)


class ScanDocumentResponse(BaseModel):
    raw_text: str | None = None
    structured_data: dict[str, Any] | None = None
    confidence: float | None = None
    model: str = "gpt-4o"
    tokens: int = 0
    document_analysis: DocumentAnalysisResponse = Field(
        default_factory=DocumentAnalysisResponse
    )


class MediaAssetResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    asset_type: str
    mime_type: str | None = None
    storage_key: str
    size_bytes: int | None = None
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    thumbnail_key: str | None = None
    ocr_text: str | None = None
    ai_tags: list | None = None
    ai_analysis: dict | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True

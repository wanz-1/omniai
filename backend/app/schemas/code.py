import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CodeProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    language: str = Field(..., min_length=1)
    framework: Optional[str] = None


class CodeProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    files: Optional[list[dict]] = None


class CodeGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    language: str = Field(..., min_length=1)
    framework: Optional[str] = None
    context_files: Optional[list[dict]] = None


class CodeExplainRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)


class CodeReviewRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)


class CodeReviewSuggestion(BaseModel):
    line: int
    severity: str
    message: str
    recommendation: Optional[str] = None


class CodeReviewResponse(BaseModel):
    suggestions: list[CodeReviewSuggestion]
    security_issues: list[dict] = []
    performance_notes: list[str] = []


class CodeGenerateResponse(BaseModel):
    code: str
    explanation: Optional[str] = None
    language: str
    tokens_used: Optional[int] = None


class CodeProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    language: str
    framework: Optional[str] = None
    files: Optional[list[dict]] = None
    project_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

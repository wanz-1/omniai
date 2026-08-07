import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CodeProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    project_id: uuid.UUID | None = None
    language: str = Field(..., min_length=1)
    framework: str | None = None


class CodeProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    files: list[dict] | None = None


class CodeGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    language: str = Field(..., min_length=1)
    framework: str | None = None
    context_files: list[dict] | None = None


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
    recommendation: str | None = None


class CodeReviewResponse(BaseModel):
    suggestions: list[CodeReviewSuggestion]
    security_issues: list[dict] = []
    performance_notes: list[str] = []


class CodeGenerateResponse(BaseModel):
    code: str
    explanation: str | None = None
    language: str
    tokens_used: int | None = None


class CodeProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    language: str
    framework: str | None = None
    files: list[dict] | None = None
    project_id: uuid.UUID | None = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

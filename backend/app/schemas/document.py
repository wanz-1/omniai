import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DocumentType, Tone


class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str | None = None
    content_type: DocumentType = DocumentType.TXT
    project_id: uuid.UUID | None = None


class DocumentUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    content: str | None = None


class HumanizeRequest(BaseModel):
    tone: Tone = Tone.PROFESSIONAL
    audience: str | None = None
    preserve_meaning: bool = True
    stream: bool = True
    ai_provider: str | None = None


class HumanizeResponse(BaseModel):
    humanized_content: str
    readability_score: float
    original_ai_score: float
    humanized_ai_score: float
    word_count: int
    changes_summary: str | None = None
    streaming: bool = False
    reading_level: str | None = None
    sentence_complexity: float | None = None
    word_diversity: float | None = None
    ai_patterns: list[str] = []
    improvements: list[str] = []
    vocabulary_score: float | None = None


class SummarizeRequest(BaseModel):
    length: str = Field(default="medium", pattern="^(short|medium|long)$")
    format: str = Field(default="paragraphs", pattern="^(paragraphs|bullets)$")


class SummarizeResponse(BaseModel):
    summary: str


class TranslateRequest(BaseModel):
    target_language: str = Field(..., min_length=2, max_length=10)


class TranslateResponse(BaseModel):
    translated_content: str
    source_language: str
    target_language: str


class GrammarCorrection(BaseModel):
    original: str
    suggestion: str
    type: str = "grammar"
    position: dict = {"start": 0, "end": 0}
    explanation: str | None = None
    severity: str = "warning"


class GrammarResponse(BaseModel):
    corrections: list[GrammarCorrection]


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str | None = None
    humanized_content: str | None = None
    content_type: str
    tone: str | None = None
    audience: str | None = None
    readability_score: float | None = None
    original_ai_score: float | None = None
    humanized_ai_score: float | None = None
    word_count: int | None = None
    language: str
    file_path: str | None = None
    file_size: int | None = None
    project_id: uuid.UUID | None = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    content: str
    change_summary: str | None = None
    ai_score: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportRequest(BaseModel):
    format: DocumentType = DocumentType.DOCX

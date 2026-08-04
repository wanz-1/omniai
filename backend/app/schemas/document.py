import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import DocumentType, Tone


class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: Optional[str] = None
    content_type: DocumentType = DocumentType.TXT
    project_id: Optional[uuid.UUID] = None


class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = None


class HumanizeRequest(BaseModel):
    tone: Tone = Tone.PROFESSIONAL
    audience: Optional[str] = None
    preserve_meaning: bool = True
    stream: bool = True
    ai_provider: Optional[str] = None


class HumanizeResponse(BaseModel):
    humanized_content: str
    readability_score: float
    original_ai_score: float
    humanized_ai_score: float
    word_count: int
    changes_summary: Optional[str] = None
    streaming: bool = False
    reading_level: Optional[str] = None
    sentence_complexity: Optional[float] = None
    word_diversity: Optional[float] = None
    ai_patterns: list[str] = []
    improvements: list[str] = []
    vocabulary_score: Optional[float] = None


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
    explanation: Optional[str] = None
    severity: str = "warning"


class GrammarResponse(BaseModel):
    corrections: list[GrammarCorrection]


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: Optional[str] = None
    humanized_content: Optional[str] = None
    content_type: str
    tone: Optional[str] = None
    audience: Optional[str] = None
    readability_score: Optional[float] = None
    original_ai_score: Optional[float] = None
    humanized_ai_score: Optional[float] = None
    word_count: Optional[int] = None
    language: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    project_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    content: str
    change_summary: Optional[str] = None
    ai_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    format: DocumentType = DocumentType.DOCX

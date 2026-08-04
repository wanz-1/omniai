import uuid
from sqlalchemy import BigInteger, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DocumentType, Tone
from app.models.base import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    humanized_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.TXT, nullable=False)
    tone: Mapped[Tone | None] = mapped_column(Enum(Tone), nullable=True)
    audience: Mapped[str | None] = mapped_column(String(100), nullable=True)
    readability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    humanized_ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("Project", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Document(id={self.id}, title={self.title})"


class DocumentVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    document = relationship("Document", back_populates="versions")

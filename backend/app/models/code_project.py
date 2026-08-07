import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class CodeProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "code_projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)
    files: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    generations = relationship("CodeGeneration", back_populates="code_project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"CodeProject(id={self.id}, name={self.name}, language={self.language})"


class CodeGeneration(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "code_generations"

    code_project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("code_projects.id"), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    generated_code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    code_project = relationship("CodeProject", back_populates="generations")

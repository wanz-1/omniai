import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class StudioProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "studio_projects"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[str] = mapped_column(String(50), default="web", nullable=False)
    frontend_framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    backend_framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    database_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="python", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="planning", nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="scratch", nullable=False)
    file_tree: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    files = relationship("StudioFile", back_populates="project", cascade="all, delete-orphan")
    builds = relationship("BuildRecord", back_populates="project", cascade="all, delete-orphan")
    deployments = relationship("StudioDeployment", back_populates="project", cascade="all, delete-orphan")
    tests = relationship("TestRun", back_populates="project", cascade="all, delete-orphan")
    scans = relationship("SecurityScan", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("StudioDocumentation", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"StudioProject(id={self.id}, name={self.name})"


class StudioFile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "studio_files"

    path: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_binary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sha_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    encoding: Mapped[str | None] = mapped_column(String(20), nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id"), nullable=False, index=True
    )

    project = relationship("StudioProject", back_populates="files")

    def __repr__(self):
        return f"StudioFile(id={self.id}, path={self.path})"


class Repository(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "repositories"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(20), default="github", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    clone_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    token: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id"), nullable=True, index=True
    )

    commits = relationship("CommitRecord", back_populates="repository", cascade="all, delete-orphan")
    branches = relationship("BranchRecord", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Repository(id={self.id}, name={self.name}, provider={self.provider})"


class CommitRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "commit_records"

    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    files_changed: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    additions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deletions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    repository = relationship("Repository", back_populates="commits")

    def __repr__(self):
        return f"CommitRecord(id={self.id}, message={self.message[:50]})"


class BranchRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "branch_records"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    head_commit_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False, index=True
    )

    repository = relationship("Repository", back_populates="branches")

    def __repr__(self):
        return f"BranchRecord(id={self.id}, name={self.name})"


class BuildRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "build_records"

    build_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    trigger: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    commit_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    log: Mapped[str | None] = mapped_column(Text, nullable=True)
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("StudioProject", back_populates="builds")

    def __repr__(self):
        return f"BuildRecord(id={self.id}, build={self.build_number}, status={self.status})"


class StudioDeployment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "studio_deployments"

    deployment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    target: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(20), default="production", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    log: Mapped[str | None] = mapped_column(Text, nullable=True)
    build_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("build_records.id"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("StudioProject", back_populates="deployments")

    def __repr__(self):
        return f"StudioDeployment(id={self.id}, target={self.target}, status={self.status})"


class TestRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "test_runs"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    test_type: Mapped[str] = mapped_column(String(30), default="unit", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    log: Mapped[str | None] = mapped_column(Text, nullable=True)
    results: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("StudioProject", back_populates="tests")

    def __repr__(self):
        return f"TestRun(id={self.id}, name={self.name}, status={self.status})"


class SecurityScan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "security_scans"

    scan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    vulnerabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity_counts: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("StudioProject", back_populates="scans")

    def __repr__(self):
        return f"SecurityScan(id={self.id}, type={self.scan_type}, score={self.risk_score})"


class StudioDocumentation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "studio_documentations"

    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)
    sections: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    project = relationship("StudioProject", back_populates="documents")

    def __repr__(self):
        return f"StudioDocumentation(id={self.id}, type={self.doc_type}, title={self.title})"

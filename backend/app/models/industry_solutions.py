import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Industry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "industries"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    packages = relationship("SolutionPackage", back_populates="industry", cascade="all, delete-orphan")
    knowledge_bases = relationship("IndustryKnowledgeBase", back_populates="industry", cascade="all, delete-orphan")
    workflows = relationship("IndustryWorkflow", back_populates="industry", cascade="all, delete-orphan")
    compliance_rules = relationship("ComplianceRule", back_populates="industry", cascade="all, delete-orphan")
    agents = relationship("IndustryAgent", back_populates="industry", cascade="all, delete-orphan")
    templates = relationship("IndustryTemplate", back_populates="industry", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Industry(id={self.id}, name={self.name}, slug={self.slug})"


class SolutionPackage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "solution_packages"

    industry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    is_installed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    agent_ids: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    workflow_ids: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    template_ids: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    industry = relationship("Industry", back_populates="packages")

    def __repr__(self):
        return f"SolutionPackage(id={self.id}, name={self.name}, industry_id={self.industry_id})"


class IndustryKnowledgeBase(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "industry_knowledge_bases"

    industry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    industry = relationship("Industry", back_populates="knowledge_bases")

    def __repr__(self):
        return f"IndustryKnowledgeBase(id={self.id}, title={self.title})"


class IndustryWorkflow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "industry_workflows"

    industry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    steps: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trigger: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    industry = relationship("Industry", back_populates="workflows")

    def __repr__(self):
        return f"IndustryWorkflow(id={self.id}, name={self.name})"


class ComplianceRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_rules"

    industry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    condition: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    action: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    industry = relationship("Industry", back_populates="compliance_rules")

    def __repr__(self):
        return f"ComplianceRule(id={self.id}, name={self.name})"


class IndustryAgent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "industry_agents"

    industry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    industry = relationship("Industry", back_populates="agents")

    def __repr__(self):
        return f"IndustryAgent(id={self.id}, name={self.name})"


class IndustryTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "industry_templates"

    industry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    variables: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    industry = relationship("Industry", back_populates="templates")

    def __repr__(self):
        return f"IndustryTemplate(id={self.id}, name={self.name})"


class IndustryAnalytic(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "industry_analytics"

    industry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dimensions: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

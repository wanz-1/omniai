import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class StartupProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "startup_projects"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planning", nullable=False)
    business_plan: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    market_research: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    brand_identity: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    technical_specs: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    generated_assets: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    products = relationship("AIGeneratedProduct", back_populates="startup", cascade="all, delete-orphan")

    def __repr__(self):
        return f"StartupProject(id={self.id}, name={self.name})"


class AIGeneratedProduct(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_generated_products"

    startup_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("startup_projects.id"), nullable=False, index=True)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_design: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    specifications: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="generated", nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    startup = relationship("StartupProject", back_populates="products")

    def __repr__(self):
        return f"AIGeneratedProduct(id={self.id}, name={self.name})"


class ProductIdea(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_ideas"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_market: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    market_research: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    user_stories: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    feature_roadmap: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    competitive_analysis: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    def __repr__(self):
        return f"ProductIdea(id={self.id}, title={self.title})"


class DesignAsset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "design_assets"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"DesignAsset(id={self.id}, name={self.name})"

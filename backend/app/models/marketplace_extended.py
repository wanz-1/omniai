import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductCategory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_categories"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True, index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    subcategories = relationship(
        "ProductCategory",
        backref=backref("parent", remote_side="ProductCategory.id"),
        foreign_keys="ProductCategory.parent_id",
    )

    def __repr__(self):
        return f"ProductCategory(id={self.id}, name={self.name})"


class ProductVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_versions"

    version: Mapped[str] = mapped_column(String(20), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    compatibility: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False, index=True
    )

    product = relationship("MarketplaceItem")

    def __repr__(self):
        return f"ProductVersion(id={self.id}, version={self.version})"


class ProductReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_reviews"

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    pros: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    cons: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    product = relationship("MarketplaceItem")
    user = relationship("User")

    def __repr__(self):
        return f"ProductReview(id={self.id}, rating={self.rating})"


class ProductAnalytic(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_analytics"

    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    installs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    refunds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False, index=True
    )

    product = relationship("MarketplaceItem")

    def __repr__(self):
        return f"ProductAnalytic(id={self.id}, date={self.date})"


class CreatorProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "creator_profiles"

    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_products: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    skills: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, unique=True
    )

    user = relationship("User")

    def __repr__(self):
        return f"CreatorProfile(id={self.id}, name={self.display_name})"


class PluginDefinition(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plugin_definitions"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plugin_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    entry_point: Mapped[str | None] = mapped_column(String(300), nullable=True)
    config_schema: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    permissions_required: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=True
    )

    author = relationship("User")

    def __repr__(self):
        return f"PluginDefinition(id={self.id}, name={self.name})"


class PluginInstallation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plugin_installations"

    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    installed_version: Mapped[str] = mapped_column(String(20), nullable=False)

    plugin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plugin_definitions.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    plugin = relationship("PluginDefinition")

    def __repr__(self):
        return f"PluginInstallation(id={self.id}, plugin={self.plugin_id})"


class VerificationResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "verification_results"

    level: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    security_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    performance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    documentation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    issues: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False, index=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    product = relationship("MarketplaceItem")

    def __repr__(self):
        return f"VerificationResult(id={self.id}, level={self.level}, status={self.status})"


class EnterpriseListing(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "enterprise_listings"

    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allowed_orgs: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    license_type: Mapped[str] = mapped_column(String(50), default="enterprise", nullable=False)
    custom_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    support_level: Mapped[str] = mapped_column(String(30), default="standard", nullable=False)
    sla_document: Mapped[str | None] = mapped_column(Text, nullable=True)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False, index=True, unique=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )

    product = relationship("MarketplaceItem")
    organization = relationship("Organization")

    def __repr__(self):
        return f"EnterpriseListing(id={self.id}, product={self.product_id})"

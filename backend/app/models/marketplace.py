import uuid
from decimal import Decimal

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MarketplaceItemStatus, MarketplaceItemType
from app.models.base import Base, TimestampMixin, UUIDMixin


class MarketplaceItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketplace_items"

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    item_type: Mapped[MarketplaceItemType] = mapped_column(
        Enum(MarketplaceItemType), nullable=False
    )
    status: Mapped[MarketplaceItemStatus] = mapped_column(
        Enum(MarketplaceItemStatus), default=MarketplaceItemStatus.DRAFT, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    price: Mapped[Decimal] = mapped_column(Float, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    preview_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    demo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    author = relationship("User")

    def __repr__(self) -> str:
        return f"MarketplaceItem(id={self.id}, name={self.name}, type={self.item_type})"


class MarketplacePurchase(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketplace_purchases"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Float, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    item = relationship("MarketplaceItem")

    def __repr__(self) -> str:
        return f"MarketplacePurchase(id={self.id}, item={self.item_id})"

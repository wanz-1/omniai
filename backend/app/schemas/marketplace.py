import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MarketplaceItemResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    item_type: str
    status: str
    name: str
    slug: str
    description: str | None = None
    short_description: str | None = None
    category: str | None = None
    tags: list | None = None
    price: Decimal
    currency: str = "USD"
    preview_image_url: str | None = None
    demo_url: str | None = None
    source_type: str | None = None
    version: str = "1.0.0"
    downloads: int = 0
    rating: float | None = None
    rating_count: int = 0
    author_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MarketplaceItemCreateRequest(BaseModel):
    item_type: str
    name: str
    slug: str
    description: str | None = None
    short_description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    price: Decimal = 0
    currency: str = "USD"
    preview_image_url: str | None = None
    demo_url: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    config: dict | None = None


class MarketplaceItemUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    price: Decimal | None = None
    preview_image_url: str | None = None
    demo_url: str | None = None


class PurchaseResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    item_name: str | None = None
    amount: Decimal
    currency: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

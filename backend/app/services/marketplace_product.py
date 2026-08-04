import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import MarketplaceItem, MarketplacePurchase
from app.models.marketplace_extended import (
    EnterpriseListing,
    ProductAnalytic,
    ProductCategory,
    ProductVersion,
    CreatorProfile,
)
from app.services.ai_service import ai_service


class MarketplaceProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, name: str, slug: str, description: str | None = None, icon: str | None = None, parent_id: uuid.UUID | None = None) -> ProductCategory:
        cat = ProductCategory(name=name, slug=slug, description=description, icon=icon, parent_id=parent_id)
        self.db.add(cat); await self.db.commit(); await self.db.refresh(cat)
        return cat

    async def list_categories(self) -> list[ProductCategory]:
        result = await self.db.execute(select(ProductCategory).where(ProductCategory.is_active == True).order_by(ProductCategory.sort_order))
        return list(result.scalars().all())

    async def publish_product(self, author_id: uuid.UUID, data: dict) -> MarketplaceItem:
        from app.models.marketplace import MarketplaceItem
        slug = data.get("name", "product").lower().replace(" ", "-") + f"-{uuid.uuid4().hex[:8]}"
        item = MarketplaceItem(
            author_id=author_id, name=data["name"], slug=slug,
            description=data.get("description"), short_description=data.get("short_description"),
            item_type=data["item_type"], category=data.get("category"),
            price=data.get("price", 0.0), tags=data.get("tags", []),
            preview_image_url=data.get("preview_image_url"), demo_url=data.get("demo_url"),
            config=data.get("config", {}), source_type=data.get("source_type"), source_id=data.get("source_id"),
        )
        self.db.add(item); await self.db.flush()

        version = ProductVersion(product_id=item.id, version="1.0.0", release_notes="Initial release")
        self.db.add(version)

        creator = await self.db.execute(select(CreatorProfile).where(CreatorProfile.user_id == author_id))
        creator_profile = creator.scalar_one_or_none()
        if creator_profile:
            creator_profile.total_products = await self.db.scalar(select(func.count(MarketplaceItem.id)).where(MarketplaceItem.author_id == author_id)) or 0

        await self.db.commit(); await self.db.refresh(item)
        return item

    async def list_products(self, category: str | None = None, item_type: str | None = None, search: str | None = None, limit: int = 50) -> list[MarketplaceItem]:
        stmt = select(MarketplaceItem).where(MarketplaceItem.status == "approved")
        if category: stmt = stmt.where(MarketplaceItem.category == category)
        if item_type: stmt = stmt.where(MarketplaceItem.item_type == item_type)
        if search: stmt = stmt.where(MarketplaceItem.name.ilike(f"%{search}%") | MarketplaceItem.description.ilike(f"%{search}%"))
        stmt = stmt.order_by(MarketplaceItem.downloads.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_product(self, product_id: uuid.UUID) -> MarketplaceItem | None:
        result = await self.db.execute(select(MarketplaceItem).where(MarketplaceItem.id == product_id))
        return result.scalar_one_or_none()

    async def get_product_versions(self, product_id: uuid.UUID) -> list[ProductVersion]:
        result = await self.db.execute(select(ProductVersion).where(ProductVersion.product_id == product_id).order_by(ProductVersion.created_at.desc()))
        return list(result.scalars().all())

    async def create_version(self, product_id: uuid.UUID, version: str, changelog: str | None = None) -> ProductVersion:
        v = ProductVersion(product_id=product_id, version=version, changelog=changelog)
        self.db.add(v)
        item_result = await self.db.execute(select(MarketplaceItem).where(MarketplaceItem.id == product_id))
        item = item_result.scalar_one_or_none()
        if item: item.version = version
        await self.db.commit(); await self.db.refresh(v)
        return v

    async def record_download(self, product_id: uuid.UUID) -> None:
        item = await self.get_product(product_id)
        if item: item.downloads = (item.downloads or 0) + 1; await self.db.commit()

    async def purchase_product(self, product_id: uuid.UUID, user_id: uuid.UUID, org_id: uuid.UUID | None = None) -> MarketplacePurchase:
        item = await self.get_product(product_id)
        if not item: raise ValueError("Product not found")
        purchase = MarketplacePurchase(item_id=product_id, user_id=user_id, organization_id=org_id, amount=item.price)
        self.db.add(purchase)

        creator = await self.db.execute(select(CreatorProfile).where(CreatorProfile.user_id == item.author_id))
        cp = creator.scalar_one_or_none()
        if cp:
            cp.total_sales += 1; cp.total_revenue += float(item.price)

        analytic = ProductAnalytic(
            product_id=product_id, date=datetime.now(timezone.utc),
            installs=1, revenue=float(item.price),
        )
        self.db.add(analytic)
        await self.db.commit(); await self.db.refresh(purchase)
        return purchase

    async def get_enterprise_listing(self, product_id: uuid.UUID, org_id: uuid.UUID) -> EnterpriseListing | None:
        result = await self.db.execute(select(EnterpriseListing).where(EnterpriseListing.product_id == product_id))
        listing = result.scalar_one_or_none()
        if listing and listing.is_private and listing.allowed_orgs:
            if str(org_id) not in [str(o) for o in listing.allowed_orgs]:
                return None
        return listing

    async def generate_sdk(self, language: str = "python", features: list[str] | None = None) -> str:
        features_str = ", ".join(features or ["marketplace", "ai_agents", "workflows"])
        messages = [
            {"role": "system", "content": f"Generate a complete {language} SDK for OmniAI platform with these features: {features_str}"},
            {"role": "user", "content": f"Generate {language} SDK with modules for: {features_str}. Include API client, authentication, error handling, and examples."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        return result.get("content", "")

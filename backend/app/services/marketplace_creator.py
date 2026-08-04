import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import MarketplaceItem, MarketplacePurchase
from app.models.marketplace_extended import CreatorProfile, ProductAnalytic


class MarketplaceCreatorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, user_id: uuid.UUID, display_name: str | None = None) -> CreatorProfile:
        result = await self.db.execute(select(CreatorProfile).where(CreatorProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile: return profile
        profile = CreatorProfile(user_id=user_id, display_name=display_name or "Creator")
        self.db.add(profile); await self.db.commit(); await self.db.refresh(profile)
        return profile

    async def update_profile(self, user_id: uuid.UUID, **kwargs) -> CreatorProfile:
        profile = await self.get_or_create_profile(user_id)
        for k, v in kwargs.items():
            if hasattr(profile, k): setattr(profile, k, v)
        await self.db.commit(); await self.db.refresh(profile)
        return profile

    async def get_dashboard(self, user_id: uuid.UUID) -> dict:
        profile = await self.get_or_create_profile(user_id)
        products_result = await self.db.execute(
            select(MarketplaceItem).where(MarketplaceItem.author_id == user_id).order_by(MarketplaceItem.created_at.desc())
        )
        products = list(products_result.scalars().all())

        sales_result = await self.db.execute(
            select(MarketplacePurchase)
            .join(MarketplaceItem, MarketplacePurchase.item_id == MarketplaceItem.id)
            .where(MarketplaceItem.author_id == user_id)
            .order_by(MarketplacePurchase.created_at.desc())
            .limit(20)
        )
        sales = list(sales_result.scalars().all())

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        analytics_result = await self.db.execute(
            select(func.sum(ProductAnalytic.views), func.sum(ProductAnalytic.installs), func.sum(ProductAnalytic.revenue))
            .where(ProductAnalytic.product_id.in_([p.id for p in products]), ProductAnalytic.date >= thirty_days_ago)
        )
        views, installs, revenue = analytics_result.one()

        return {
            "total_products": len(products),
            "total_sales": profile.total_sales,
            "total_revenue": profile.total_revenue,
            "average_rating": profile.average_rating,
            "recent_sales": [{"id": str(s.id), "amount": s.amount, "date": s.created_at.isoformat() if s.created_at else None} for s in sales[:5]],
            "products": [{"id": str(p.id), "name": p.name, "type": p.item_type, "status": p.status, "downloads": p.downloads, "price": p.price, "rating": p.rating} for p in products],
            "analytics": {"views_last_30d": int(views or 0), "installs_last_30d": int(installs or 0), "revenue_last_30d": float(revenue or 0.0)},
        }

    async def get_analytics(self, product_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(ProductAnalytic).where(ProductAnalytic.product_id == product_id).order_by(ProductAnalytic.date.desc()).limit(30)
        )
        analytics = list(result.scalars().all())
        return {
            "daily": [{"date": a.date.isoformat() if a.date else None, "views": a.views, "installs": a.installs, "revenue": a.revenue} for a in analytics],
            "totals": {"views": sum(a.views for a in analytics), "installs": sum(a.installs for a in analytics), "revenue": sum(a.revenue for a in analytics)},
        }

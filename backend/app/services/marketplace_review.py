import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import MarketplaceItem
from app.models.marketplace_extended import ProductReview, CreatorProfile


class MarketplaceReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(self, product_id: uuid.UUID, user_id: uuid.UUID, rating: int, title: str | None = None, content: str | None = None, pros: list[str] | None = None, cons: list[str] | None = None) -> ProductReview:
        review = ProductReview(
            product_id=product_id, user_id=user_id, rating=rating,
            title=title, content=content, pros=pros or [], cons=cons or [],
        )
        self.db.add(review)
        await self._update_product_rating(product_id)
        await self._update_creator_rating(product_id)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def get_product_reviews(self, product_id: uuid.UUID, limit: int = 50) -> list[ProductReview]:
        result = await self.db.execute(
            select(ProductReview).where(ProductReview.product_id == product_id, ProductReview.is_approved == True).order_by(ProductReview.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_reviews(self, user_id: uuid.UUID) -> list[ProductReview]:
        result = await self.db.execute(
            select(ProductReview).where(ProductReview.user_id == user_id).order_by(ProductReview.created_at.desc())
        )
        return list(result.scalars().all())

    async def _update_product_rating(self, product_id: uuid.UUID) -> None:
        stats = await self.db.execute(
            select(func.avg(ProductReview.rating), func.count(ProductReview.id))
            .where(ProductReview.product_id == product_id, ProductReview.is_approved == True)
        )
        avg, count = stats.one()
        item = await self.db.execute(select(MarketplaceItem).where(MarketplaceItem.id == product_id))
        item_obj = item.scalar_one_or_none()
        if item_obj:
            item_obj.rating = round(float(avg), 2) if avg else None
            item_obj.rating_count = count or 0

    async def _update_creator_rating(self, product_id: uuid.UUID) -> None:
        item = await self.db.execute(select(MarketplaceItem).where(MarketplaceItem.id == product_id))
        item_obj = item.scalar_one_or_none()
        if not item_obj: return

        creator = await self.db.execute(select(CreatorProfile).where(CreatorProfile.user_id == item_obj.author_id))
        cp = creator.scalar_one_or_none()
        if cp:
            result = await self.db.execute(
                select(func.avg(ProductReview.rating))
                .join(MarketplaceItem, ProductReview.product_id == MarketplaceItem.id)
                .where(MarketplaceItem.author_id == item_obj.author_id, ProductReview.is_approved == True)
            )
            avg = result.scalar()
            cp.average_rating = round(float(avg), 2) if avg else None

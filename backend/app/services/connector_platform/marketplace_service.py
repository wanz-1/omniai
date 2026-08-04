import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_connector_platform import (
    ConnectorDefinition, MarketplaceConnector,
)


class MarketplaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_marketplace_items(self, category: str | None = None, search: str | None = None) -> list[dict]:
        q = select(
            ConnectorDefinition, MarketplaceConnector
        ).join(
            MarketplaceConnector, ConnectorDefinition.id == MarketplaceConnector.connector_id
        ).where(
            ConnectorDefinition.is_active == True
        )
        if category:
            q = q.where(ConnectorDefinition.category == category)
        if search:
            q = q.where(ConnectorDefinition.name.ilike(f"%{search}%"))
        q = q.order_by(MarketplaceConnector.download_count.desc())
        rows = await self.db.execute(q)
        results = []
        for definition, mc in rows.all():
            results.append({
                "id": str(mc.id),
                "connector_id": str(definition.id),
                "name": definition.name,
                "description": definition.description,
                "category": definition.category,
                "icon_url": definition.icon_url,
                "auth_type": definition.auth_type,
                "is_verified": mc.is_verified,
                "rating": mc.rating,
                "download_count": mc.download_count,
                "pricing_tier": mc.pricing_tier,
                "price": mc.price,
                "publisher": definition.publisher,
            })
        return results

    async def get_marketplace_item(self, item_id: uuid.UUID) -> dict | None:
        rows = await self.db.execute(
            select(ConnectorDefinition, MarketplaceConnector).join(
                MarketplaceConnector, ConnectorDefinition.id == MarketplaceConnector.connector_id
            ).where(MarketplaceConnector.id == item_id)
        )
        row = rows.one_or_none()
        if not row:
            return None
        definition, mc = row
        return {
            "id": str(mc.id),
            "connector_id": str(definition.id),
            "name": definition.name,
            "description": definition.description,
            "category": definition.category,
            "icon_url": definition.icon_url,
            "version": definition.version,
            "auth_type": definition.auth_type,
            "permissions": definition.permissions,
            "actions": definition.actions,
            "events": definition.events,
            "config_schema": definition.config_schema,
            "is_verified": mc.is_verified,
            "rating": mc.rating,
            "download_count": mc.download_count,
            "reviews": mc.reviews,
            "pricing_tier": mc.pricing_tier,
            "price": mc.price,
            "documentation": mc.documentation,
            "support_url": mc.support_url,
            "publisher": definition.publisher,
        }

    async def record_download(self, item_id: uuid.UUID) -> None:
        rows = await self.db.execute(select(MarketplaceConnector).where(MarketplaceConnector.id == item_id))
        mc = rows.scalar_one_or_none()
        if mc:
            mc.download_count = (mc.download_count or 0) + 1
            await self.db.commit()

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_extended import PluginDefinition, PluginInstallation


class MarketplacePluginService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_plugin(
        self, name: str, slug: str, plugin_type: str, author_id: uuid.UUID,
        description: str | None = None, entry_point: str | None = None,
        config_schema: dict | None = None, permissions: list[str] | None = None,
        source_url: str | None = None, docs_url: str | None = None,
        product_id: uuid.UUID | None = None,
    ) -> PluginDefinition:
        plugin = PluginDefinition(
            name=name, slug=slug, plugin_type=plugin_type, author_id=author_id,
            description=description, entry_point=entry_point,
            config_schema=config_schema or {}, permissions_required=permissions or [],
            source_url=source_url, documentation_url=docs_url, product_id=product_id,
        )
        self.db.add(plugin)
        await self.db.commit()
        await self.db.refresh(plugin)
        return plugin

    async def install_plugin(self, plugin_id: uuid.UUID, user_id: uuid.UUID, org_id: uuid.UUID | None = None, config: dict | None = None) -> PluginInstallation:
        plugin = await self.db.execute(select(PluginDefinition).where(PluginDefinition.id == plugin_id))
        p = plugin.scalar_one_or_none()
        if not p:
            raise ValueError("Plugin not found")
        existing = await self.db.execute(
            select(PluginInstallation).where(PluginInstallation.plugin_id == plugin_id, PluginInstallation.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Plugin already installed")
        inst = PluginInstallation(
            plugin_id=plugin_id, user_id=user_id, organization_id=org_id,
            config=config or {}, installed_version=p.version,
        )
        self.db.add(inst)
        await self.db.commit()
        await self.db.refresh(inst)
        return inst

    async def uninstall_plugin(self, installation_id: uuid.UUID) -> None:
        result = await self.db.execute(select(PluginInstallation).where(PluginInstallation.id == installation_id))
        inst = result.scalar_one_or_none()
        if inst:
            await self.db.delete(inst)
            await self.db.commit()

    async def list_plugins(self, plugin_type: str | None = None) -> list[PluginDefinition]:
        stmt = select(PluginDefinition).where(PluginDefinition.is_active.is_(True))
        if plugin_type:
            stmt = stmt.where(PluginDefinition.plugin_type == plugin_type)
        stmt = stmt.order_by(PluginDefinition.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_plugins(self, user_id: uuid.UUID) -> list[PluginInstallation]:
        result = await self.db.execute(
            select(PluginInstallation).where(PluginInstallation.user_id == user_id).order_by(PluginInstallation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_org_plugins(self, org_id: uuid.UUID) -> list[PluginInstallation]:
        result = await self.db.execute(
            select(PluginInstallation).where(PluginInstallation.organization_id == org_id).order_by(PluginInstallation.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_plugin_config(self, installation_id: uuid.UUID, config: dict) -> PluginInstallation:
        result = await self.db.execute(select(PluginInstallation).where(PluginInstallation.id == installation_id))
        inst = result.scalar_one_or_none()
        if inst:
            inst.config = config
            await self.db.commit()
            await self.db.refresh(inst)
        return inst

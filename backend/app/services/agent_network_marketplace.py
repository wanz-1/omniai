import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentProfile
from app.models.agent_network import AgentTeam
from app.models.marketplace import MarketplaceItem, MarketplacePurchase
from app.services.ai_service import ai_service


class AgentNetworkMarketplaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish_agent(self, agent_id: uuid.UUID, price: float = 0.0, category: str = "general") -> MarketplaceItem:
        result = await self.db.execute(select(AgentProfile).where(AgentProfile.id == agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError("Agent not found")

        item = MarketplaceItem(
            author_id=agent.user_id,
            item_type="agent",
            status="approved",
            name=agent.name,
            slug=f"agent-{agent.id}",
            description=agent.description,
            category=category,
            price=price,
            source_type="agent_profile",
            source_id=agent.id,
            config={
                "role": agent.role,
                "system_prompt": agent.system_prompt,
                "model": agent.model,
                "temperature": agent.temperature,
                "skills": [s.name for s in agent.skills] if hasattr(agent, "skills") else [],
            },
        )
        self.db.add(item)
        agent.marketplace_listed = True
        agent.price = price
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def publish_team_template(self, team_id: uuid.UUID, price: float = 0.0) -> MarketplaceItem:
        result = await self.db.execute(select(AgentTeam).where(AgentTeam.id == team_id))
        team = result.scalar_one_or_none()
        if not team:
            raise ValueError("Team not found")

        item = MarketplaceItem(
            author_id=team.user_id,
            item_type="template",
            status="approved",
            name=f"Team: {team.name}",
            slug=f"team-{team.id}",
            description=team.description,
            category="team_template",
            price=price,
            source_type="agent_team",
            source_id=team.id,
            config={"purpose": team.purpose, "team_config": team.config},
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def clone_to_organization(self, item_id: uuid.UUID, organization_id: uuid.UUID) -> dict:
        result = await self.db.execute(select(MarketplaceItem).where(MarketplaceItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError("Marketplace item not found")

        if item.source_type == "agent_profile" and item.source_id:
            source_result = await self.db.execute(select(AgentProfile).where(AgentProfile.id == item.source_id))
            source = source_result.scalar_one_or_none()
            if source:
                cloned = AgentProfile(
                    name=f"{source.name} (Cloned)",
                    role=source.role,
                    description=source.description,
                    system_prompt=source.system_prompt,
                    model=source.model,
                    temperature=source.temperature,
                    status="draft",
                    user_id=None,
                    organization_id=organization_id,
                    config=source.config,
                )
                self.db.add(cloned)
                await self.db.flush()
                return {"type": "agent", "id": str(cloned.id), "name": cloned.name}

        elif item.source_type == "agent_team" and item.source_id:
            source_result = await self.db.execute(select(AgentTeam).where(AgentTeam.id == item.source_id))
            source = source_result.scalar_one_or_none()
            if source:
                cloned = AgentTeam(
                    name=f"{source.name} (Clone)",
                    description=source.description,
                    purpose=source.purpose,
                    user_id=None,
                    organization_id=organization_id,
                    config=source.config,
                )
                self.db.add(cloned)
                await self.db.flush()
                return {"type": "team", "id": str(cloned.id), "name": cloned.name}

        raise ValueError("Cannot clone: unknown source type")

    async def get_marketplace_agents(self, category: str | None = None, limit: int = 50) -> list[MarketplaceItem]:
        stmt = select(MarketplaceItem).where(
            MarketplaceItem.status == "approved",
            MarketplaceItem.item_type == "agent",
        )
        if category:
            stmt = stmt.where(MarketplaceItem.category == category)
        stmt = stmt.order_by(MarketplaceItem.downloads.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_marketplace_templates(self, category: str | None = None, limit: int = 50) -> list[MarketplaceItem]:
        stmt = select(MarketplaceItem).where(
            MarketplaceItem.status == "approved",
            MarketplaceItem.item_type == "template",
        )
        if category:
            stmt = stmt.where(MarketplaceItem.category == category)
        stmt = stmt.order_by(MarketplaceItem.downloads.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

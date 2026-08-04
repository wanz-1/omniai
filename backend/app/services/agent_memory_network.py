import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_network import AgentMemoryNetwork


class AgentMemoryNetworkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(
        self,
        key: str,
        content: str,
        memory_type: str = "fact",
        category: str | None = None,
        importance: int = 1,
        visibility: str = "team",
        source: str | None = None,
        team_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> AgentMemoryNetwork:
        entry = AgentMemoryNetwork(
            key=key,
            content=content,
            memory_type=memory_type,
            category=category,
            importance=importance,
            visibility=visibility,
            source=source,
            team_id=team_id,
            organization_id=organization_id,
            agent_id=agent_id,
            user_id=user_id,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_by_key(self, key: str, team_id: uuid.UUID | None = None) -> AgentMemoryNetwork | None:
        query = select(AgentMemoryNetwork).where(AgentMemoryNetwork.key == key)
        if team_id:
            query = query.where(AgentMemoryNetwork.team_id == team_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        query_text: str,
        team_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[AgentMemoryNetwork]:
        stmt = select(AgentMemoryNetwork)
        if team_id:
            stmt = stmt.where(AgentMemoryNetwork.team_id == team_id)
        if organization_id:
            stmt = stmt.where(AgentMemoryNetwork.organization_id == organization_id)

        stmt = stmt.where(
            AgentMemoryNetwork.key.ilike(f"%{query_text}%") |
            AgentMemoryNetwork.content.ilike(f"%{query_text}%") |
            AgentMemoryNetwork.category.ilike(f"%{query_text}%")
        )
        stmt = stmt.order_by(AgentMemoryNetwork.importance.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_team_memory(self, team_id: uuid.UUID, limit: int = 50) -> list[AgentMemoryNetwork]:
        result = await self.db.execute(
            select(AgentMemoryNetwork)
            .where(AgentMemoryNetwork.team_id == team_id)
            .order_by(AgentMemoryNetwork.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_organization_memory(self, organization_id: uuid.UUID, limit: int = 50) -> list[AgentMemoryNetwork]:
        result = await self.db.execute(
            select(AgentMemoryNetwork)
            .where(AgentMemoryNetwork.organization_id == organization_id)
            .order_by(AgentMemoryNetwork.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete(self, memory_id: uuid.UUID) -> bool:
        result = await self.db.execute(select(AgentMemoryNetwork).where(AgentMemoryNetwork.id == memory_id))
        entry = result.scalar_one_or_none()
        if entry:
            await self.db.delete(entry)
            await self.db.commit()
            return True
        return False

    async def build_context(self, team_id: uuid.UUID | None = None, org_id: uuid.UUID | None = None) -> str:
        memories = []
        if team_id:
            memories.extend(await self.get_team_memory(team_id, 20))
        if org_id:
            memories.extend(await self.get_organization_memory(org_id, 20))

        if not memories:
            return ""

        context_parts = []
        for m in memories[:30]:
            context_parts.append(f"[{m.memory_type.upper()}] {m.key}: {m.content[:300]}")
        return "\n".join(context_parts)

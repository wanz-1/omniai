import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_collaboration import (
    CollaborationSession, CollaborationAgent, AgentSessionLink, MultimodalMessage,
)
from app.services.ai_service import ai_service


class CollaborationAgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(self, org_id: uuid.UUID, name: str, agent_type: str, capabilities: list | None, config: dict | None, created_by: uuid.UUID) -> CollaborationAgent:
        agent = CollaborationAgent(
            organization_id=org_id, name=name, agent_type=agent_type,
            capabilities=capabilities or [], config=config or {},
            created_by=created_by,
        )
        self.db.add(agent); await self.db.commit(); await self.db.refresh(agent)
        return agent

    async def list_agents(self, org_id: uuid.UUID) -> list[CollaborationAgent]:
        rows = await self.db.execute(
            select(CollaborationAgent).where(CollaborationAgent.organization_id == org_id, CollaborationAgent.is_active == True)
        )
        return list(rows.scalars().all())

    async def join_session(self, agent_id: uuid.UUID, session_id: uuid.UUID, role: str = "assistant") -> AgentSessionLink:
        link = AgentSessionLink(agent_id=agent_id, session_id=session_id, role=role)
        self.db.add(link); await self.db.commit(); await self.db.refresh(link)
        msg = MultimodalMessage(
            session_id=session_id, sender_id=agent_id,
            message_type="system", content=f"AI agent joined the session as {role}",
        )
        self.db.add(msg); await self.db.commit()
        return link

    async def agent_chat(self, session_id: uuid.UUID, agent_id: uuid.UUID, message: str) -> str:
        rows = await self.db.execute(select(MultimodalMessage).where(MultimodalMessage.session_id == session_id).order_by(MultimodalMessage.created_at.desc()).limit(20))
        recent = rows.scalars().all()
        context = "\n".join([f"[{m.message_type}] {m.content or '(media)'}" for m in reversed(recent)])
        prompt = f"You are a collaboration AI agent participating in a session.\nRecent context:\n{context}\n\nUser message: {message}\n\nRespond helpfully:"
        result = await ai_service.complete(prompt) or ""
        msg = MultimodalMessage(
            session_id=session_id, sender_id=agent_id,
            message_type="text", content=result,
        )
        self.db.add(msg); await self.db.commit()
        return result

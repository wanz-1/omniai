import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_network import AgentMessage
from app.services.ai_service import ai_service


COMMUNICATION_SYSTEM_PROMPT = """You are an AI agent messaging coordinator. 
Format agent-to-agent communications clearly and actionably.
Always include: key information, required action, deadline if any, and context."""


class AgentCommunicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_message(
        self,
        sender_id: uuid.UUID,
        receiver_id: uuid.UUID,
        content: str,
        message_type: str = "direct",
        task_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> AgentMessage:
        formatted = await self._format_message(content, message_type)
        msg = AgentMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=formatted,
            message_type=message_type,
            status="sent",
            task_id=task_id,
            team_id=team_id,
            meta_data=metadata or {},
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def send_broadcast(
        self,
        sender_id: uuid.UUID,
        receiver_ids: list[uuid.UUID],
        content: str,
        message_type: str = "broadcast",
        team_id: uuid.UUID | None = None,
    ) -> list[AgentMessage]:
        messages = []
        for rid in receiver_ids:
            msg = await self.send_message(sender_id, rid, content, message_type, team_id=team_id)
            messages.append(msg)
        return messages

    async def get_conversation(
        self,
        agent_id_1: uuid.UUID,
        agent_id_2: uuid.UUID,
        limit: int = 50,
    ) -> list[AgentMessage]:
        result = await self.db.execute(
            select(AgentMessage)
            .where(
                or_(
                    and_(AgentMessage.sender_id == agent_id_1, AgentMessage.receiver_id == agent_id_2),
                    and_(AgentMessage.sender_id == agent_id_2, AgentMessage.receiver_id == agent_id_1),
                )
            )
            .order_by(AgentMessage.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_team_messages(self, team_id: uuid.UUID, limit: int = 100) -> list[AgentMessage]:
        result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.team_id == team_id)
            .order_by(AgentMessage.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_read(self, message_id: uuid.UUID) -> None:
        result = await self.db.execute(select(AgentMessage).where(AgentMessage.id == message_id))
        msg = result.scalar_one_or_none()
        if msg:
            msg.status = "read"
            msg.read_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def delegate_task(
        self,
        assignor_id: uuid.UUID,
        assignee_id: uuid.UUID,
        task_description: str,
        task_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> AgentMessage:
        content = f"TASK DELEGATION:\n{task_description}\n\nPlease complete this task and report back with results."
        return await self.send_message(
            sender_id=assignor_id,
            receiver_id=assignee_id,
            content=content,
            message_type="task_delegation",
            task_id=task_id,
            team_id=team_id,
            meta_data={"delegation_type": "task", "status": "pending"},
        )

    async def _format_message(self, content: str, message_type: str) -> str:
        if message_type in ("direct", "broadcast"):
            return content
        messages = [
            {"role": "system", "content": COMMUNICATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Format this {message_type} message:\n\n{content}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o-mini", temperature=0.3)
        return result.get("content", content)

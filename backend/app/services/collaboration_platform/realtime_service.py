import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_collaboration import (
    MultimodalMessage,
    SessionParticipant,
)
from app.services.ai_service import ai_service


class RealtimeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_presence(self, session_id: uuid.UUID) -> list[dict]:
        rows = await self.db.execute(
            select(SessionParticipant).where(SessionParticipant.session_id == session_id, SessionParticipant.is_present.is_(True))
        )
        return [{"user_id": str(p.user_id), "role": p.role, "joined_at": p.joined_at.isoformat() if p.joined_at else None} for p in rows.scalars().all()]

    async def broadcast(self, session_id: uuid.UUID, sender_id: uuid.UUID, event_type: str, payload: dict) -> MultimodalMessage:
        msg = MultimodalMessage(
            session_id=session_id, sender_id=sender_id,
            message_type="realtime", content=event_type,
            meta_data=payload,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_recent_activity(self, session_id: uuid.UUID, since: datetime | None = None, limit: int = 50) -> list[MultimodalMessage]:
        q = select(MultimodalMessage).where(MultimodalMessage.session_id == session_id)
        if since:
            q = q.where(MultimodalMessage.created_at >= since)
        q = q.order_by(MultimodalMessage.created_at.desc()).limit(limit)
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def ai_meeting_notes(self, session_id: uuid.UUID) -> str:
        rows = await self.db.execute(
            select(MultimodalMessage).where(MultimodalMessage.session_id == session_id).order_by(MultimodalMessage.created_at.asc())
        )
        messages = rows.scalars().all()
        transcript = "\n".join([f"[{m.message_type}] {m.content or ''}" for m in messages if m.content])
        prompt = f"Generate real-time meeting notes from this session transcript:\n\n{transcript}"
        return await ai_service.complete(prompt) or ""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_collaboration import ScreenShareSession


class ScreenShareService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start(self, session_id: uuid.UUID, host_id: uuid.UUID, stream_url: str | None = None) -> ScreenShareSession:
        ss = ScreenShareSession(
            session_id=session_id, host_id=host_id,
            stream_url=stream_url, started_at=datetime.utcnow(),
        )
        self.db.add(ss)
        await self.db.commit()
        await self.db.refresh(ss)
        return ss

    async def stop(self, share_id: uuid.UUID) -> ScreenShareSession | None:
        rows = await self.db.execute(select(ScreenShareSession).where(ScreenShareSession.id == share_id))
        ss = rows.scalar_one_or_none()
        if not ss:
            return None
        ss.is_active = False
        ss.ended_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(ss)
        return ss

    async def get_by_session(self, session_id: uuid.UUID) -> list[ScreenShareSession]:
        rows = await self.db.execute(
            select(ScreenShareSession).where(ScreenShareSession.session_id == session_id).order_by(ScreenShareSession.created_at.desc())
        )
        return list(rows.scalars().all())

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_collaboration import WhiteboardSession
from app.services.ai_service import ai_service


class WhiteboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session_id: uuid.UUID, title: str, created_by: uuid.UUID) -> WhiteboardSession:
        wb = WhiteboardSession(session_id=session_id, title=title, created_by=created_by)
        self.db.add(wb)
        await self.db.commit()
        await self.db.refresh(wb)
        return wb

    async def update(self, whiteboard_id: uuid.UUID, strokes: list | None, shapes: list | None, annotations: list | None) -> WhiteboardSession | None:
        rows = await self.db.execute(select(WhiteboardSession).where(WhiteboardSession.id == whiteboard_id))
        wb = rows.scalar_one_or_none()
        if not wb:
            return None
        if strokes is not None:
            wb.strokes = strokes
        if shapes is not None:
            wb.shapes = shapes
        if annotations is not None:
            wb.annotations = annotations
        await self.db.commit()
        await self.db.refresh(wb)
        return wb

    async def get(self, whiteboard_id: uuid.UUID) -> WhiteboardSession | None:
        rows = await self.db.execute(select(WhiteboardSession).where(WhiteboardSession.id == whiteboard_id))
        return rows.scalar_one_or_none()

    async def list_by_session(self, session_id: uuid.UUID) -> list[WhiteboardSession]:
        rows = await self.db.execute(select(WhiteboardSession).where(WhiteboardSession.session_id == session_id))
        return list(rows.scalars().all())

    async def lock(self, whiteboard_id: uuid.UUID, locked: bool) -> WhiteboardSession | None:
        rows = await self.db.execute(select(WhiteboardSession).where(WhiteboardSession.id == whiteboard_id))
        wb = rows.scalar_one_or_none()
        if not wb:
            return None
        wb.is_locked = locked
        await self.db.commit()
        await self.db.refresh(wb)
        return wb

    async def ai_suggest(self, whiteboard_id: uuid.UUID, prompt: str) -> str:
        rows = await self.db.execute(select(WhiteboardSession).where(WhiteboardSession.id == whiteboard_id))
        wb = rows.scalar_one_or_none()
        if not wb:
            return "Whiteboard not found"
        context = f"Whiteboard: {wb.title}\nStrokes: {len(wb.strokes)} shapes: {len(wb.shapes)}\nUser request: {prompt}"
        result = await ai_service.complete(f"Analyze this whiteboard and provide suggestions:\n{context}")
        return result or ""

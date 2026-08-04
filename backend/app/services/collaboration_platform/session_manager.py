import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_collaboration import (
    CollaborationSession, SessionParticipant, MultimodalMessage,
)
from app.services.ai_service import ai_service


class SessionManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, org_id: uuid.UUID, title: str, session_type: str, description: str | None, created_by: uuid.UUID, participant_ids: list[uuid.UUID] | None = None) -> CollaborationSession:
        session = CollaborationSession(
            organization_id=org_id, title=title, session_type=session_type,
            status="scheduled", description=description, created_by=created_by,
        )
        self.db.add(session); await self.db.commit(); await self.db.refresh(session)
        if participant_ids:
            for uid in participant_ids:
                self.db.add(SessionParticipant(session_id=session.id, user_id=uid, role="participant"))
            await self.db.commit()
        return session

    async def list_sessions(self, org_id: uuid.UUID, session_type: str | None = None, status: str | None = None) -> list[CollaborationSession]:
        q = select(CollaborationSession).where(CollaborationSession.organization_id == org_id)
        if session_type: q = q.where(CollaborationSession.session_type == session_type)
        if status: q = q.where(CollaborationSession.status == status)
        q = q.order_by(CollaborationSession.created_at.desc())
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def get_session(self, session_id: uuid.UUID) -> CollaborationSession | None:
        rows = await self.db.execute(select(CollaborationSession).where(CollaborationSession.id == session_id))
        return rows.scalar_one_or_none()

    async def start_session(self, session_id: uuid.UUID) -> CollaborationSession | None:
        rows = await self.db.execute(select(CollaborationSession).where(CollaborationSession.id == session_id))
        s = rows.scalar_one_or_none()
        if s: s.status = "active"; s.started_at = datetime.utcnow(); await self.db.commit(); await self.db.refresh(s)
        return s

    async def end_session(self, session_id: uuid.UUID) -> CollaborationSession | None:
        rows = await self.db.execute(select(CollaborationSession).where(CollaborationSession.id == session_id))
        s = rows.scalar_one_or_none()
        if s: s.status = "completed"; s.ended_at = datetime.utcnow(); await self.db.commit(); await self.db.refresh(s)
        return s

    async def join_session(self, session_id: uuid.UUID, user_id: uuid.UUID, role: str = "participant") -> SessionParticipant:
        rows = await self.db.execute(select(SessionParticipant).where(SessionParticipant.session_id == session_id, SessionParticipant.user_id == user_id))
        existing = rows.scalar_one_or_none()
        if existing:
            existing.is_present = True; existing.joined_at = datetime.utcnow()
            await self.db.commit(); await self.db.refresh(existing)
            return existing
        p = SessionParticipant(session_id=session_id, user_id=user_id, role=role, joined_at=datetime.utcnow(), is_present=True)
        self.db.add(p); await self.db.commit(); await self.db.refresh(p)
        return p

    async def leave_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        rows = await self.db.execute(select(SessionParticipant).where(SessionParticipant.session_id == session_id, SessionParticipant.user_id == user_id))
        p = rows.scalar_one_or_none()
        if not p: return False
        p.is_present = False; p.left_at = datetime.utcnow(); await self.db.commit()
        return True

    async def get_participants(self, session_id: uuid.UUID) -> list[SessionParticipant]:
        rows = await self.db.execute(select(SessionParticipant).where(SessionParticipant.session_id == session_id))
        return list(rows.scalars().all())

    async def send_message(self, session_id: uuid.UUID, sender_id: uuid.UUID, message_type: str, content: str | None, media_url: str | None = None, media_type: str | None = None, duration_seconds: float | None = None, parent_id: uuid.UUID | None = None) -> MultimodalMessage:
        msg = MultimodalMessage(
            session_id=session_id, sender_id=sender_id, message_type=message_type,
            content=content, media_url=media_url, media_type=media_type,
            duration_seconds=duration_seconds, parent_id=parent_id,
        )
        self.db.add(msg); await self.db.commit(); await self.db.refresh(msg)
        return msg

    async def get_messages(self, session_id: uuid.UUID, limit: int = 100) -> list[MultimodalMessage]:
        rows = await self.db.execute(
            select(MultimodalMessage).where(MultimodalMessage.session_id == session_id)
            .order_by(MultimodalMessage.created_at.asc()).limit(limit)
        )
        return list(rows.scalars().all())

    async def get_dashboard(self, org_id: uuid.UUID) -> dict:
        total_q = await self.db.execute(select(func.count(CollaborationSession.id)).where(CollaborationSession.organization_id == org_id))
        total = total_q.scalar() or 0
        active_q = await self.db.execute(select(func.count(CollaborationSession.id)).where(CollaborationSession.organization_id == org_id, CollaborationSession.status == "active"))
        active = active_q.scalar() or 0
        parts_q = await self.db.execute(select(func.count(SessionParticipant.id)).select_from(SessionParticipant).join(CollaborationSession).where(CollaborationSession.organization_id == org_id))
        parts = parts_q.scalar() or 0
        msgs_q = await self.db.execute(select(func.count(MultimodalMessage.id)).select_from(MultimodalMessage).join(CollaborationSession).where(CollaborationSession.organization_id == org_id))
        msgs = msgs_q.scalar() or 0
        from app.models.v5_collaboration import SessionRecording, WhiteboardSession
        recs_q = await self.db.execute(select(func.count(SessionRecording.id)).select_from(SessionRecording).join(CollaborationSession).where(CollaborationSession.organization_id == org_id))
        recs = recs_q.scalar() or 0
        wb_q = await self.db.execute(select(func.count(WhiteboardSession.id)).select_from(WhiteboardSession).join(CollaborationSession).where(CollaborationSession.organization_id == org_id))
        wbs = wb_q.scalar() or 0
        type_q = await self.db.execute(select(CollaborationSession.session_type, func.count(CollaborationSession.id)).where(CollaborationSession.organization_id == org_id).group_by(CollaborationSession.session_type))
        by_type = {row[0]: row[1] for row in type_q.all()}
        return dict(total_sessions=total, active_sessions=active, total_participants=parts, total_messages=msgs, total_recordings=recs, total_whiteboards=wbs, by_type=by_type)

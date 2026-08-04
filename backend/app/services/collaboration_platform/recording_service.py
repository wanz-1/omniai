import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_collaboration import SessionRecording
from app.services.ai_service import ai_service


class RecordingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_recording(self, session_id: uuid.UUID, recording_type: str) -> SessionRecording:
        rec = SessionRecording(
            session_id=session_id, recording_type=recording_type,
            status="recording", started_at=datetime.utcnow(),
        )
        self.db.add(rec); await self.db.commit(); await self.db.refresh(rec)
        return rec

    async def stop_recording(self, recording_id: uuid.UUID, file_url: str | None = None, duration: float | None = None, file_size: int | None = None) -> SessionRecording | None:
        rows = await self.db.execute(select(SessionRecording).where(SessionRecording.id == recording_id))
        rec = rows.scalar_one_or_none()
        if not rec: return None
        rec.status = "completed"; rec.ended_at = datetime.utcnow()
        if file_url: rec.file_url = file_url
        if duration: rec.duration_seconds = duration
        if file_size: rec.file_size = file_size
        await self.db.commit(); await self.db.refresh(rec)
        return rec

    async def list_by_session(self, session_id: uuid.UUID) -> list[SessionRecording]:
        rows = await self.db.execute(
            select(SessionRecording).where(SessionRecording.session_id == session_id).order_by(SessionRecording.created_at.desc())
        )
        return list(rows.scalars().all())

    async def transcribe(self, recording_id: uuid.UUID) -> str:
        rows = await self.db.execute(select(SessionRecording).where(SessionRecording.id == recording_id))
        rec = rows.scalar_one_or_none()
        if not rec: return "Recording not found"
        prompt = f"Generate a transcript for a {rec.recording_type} recording (duration: {rec.duration_seconds or 'unknown'}s)"
        transcript = await ai_service.complete(prompt) or ""
        rec.transcript = transcript; rec.status = "completed"
        await self.db.commit()
        return transcript

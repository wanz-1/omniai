import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_collaboration import CollaborationSession, MultimodalMessage, SessionRecording, AIMeetingInsight
from app.services.ai_service import ai_service


class MeetingIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_insights(self, session_id: uuid.UUID, org_id: uuid.UUID) -> AIMeetingInsight:
        rows = await self.db.execute(select(CollaborationSession).where(CollaborationSession.id == session_id))
        session = rows.scalar_one_or_none()
        if not session: raise ValueError("Session not found")
        msgs_rows = await self.db.execute(
            select(MultimodalMessage).where(MultimodalMessage.session_id == session_id).order_by(MultimodalMessage.created_at.asc())
        )
        messages = msgs_rows.scalars().all()
        transcript = "\n".join([f"[{m.message_type}] User {m.sender_id}: {m.content or '(media)'}" for m in messages if m.content])
        prompt = f"Analyze this meeting/collaboration session and provide:\n1. Executive summary\n2. Action items\n3. Key decisions made\n4. Topics discussed\n5. Sentiment analysis\n6. Key insights\n\nSession: {session.title}\nTranscript:\n{transcript}"
        analysis = await ai_service.complete(prompt) or ""
        insight = AIMeetingInsight(
            session_id=session_id, organization_id=org_id,
            summary=analysis[:500] if analysis else None,
            transcript_full=transcript, action_items=[], decisions=[],
            topics=[], sentiment="neutral", key_insights=[analysis] if analysis else [],
            participants_summary=[], generated_at=datetime.utcnow(),
        )
        self.db.add(insight); await self.db.commit(); await self.db.refresh(insight)
        return insight

    async def get_insights(self, session_id: uuid.UUID) -> AIMeetingInsight | None:
        rows = await self.db.execute(
            select(AIMeetingInsight).where(AIMeetingInsight.session_id == session_id)
            .order_by(AIMeetingInsight.created_at.desc()).limit(1)
        )
        return rows.scalar_one_or_none()

    async def transcribe_recording(self, recording_id: uuid.UUID, audio_text: str) -> SessionRecording | None:
        rows = await self.db.execute(select(SessionRecording).where(SessionRecording.id == recording_id))
        rec = rows.scalar_one_or_none()
        if not rec: return None
        rec.transcript = audio_text; rec.status = "completed"; rec.ended_at = datetime.utcnow()
        await self.db.commit(); await self.db.refresh(rec)
        return rec

    async def list_recordings(self, session_id: uuid.UUID) -> list[SessionRecording]:
        rows = await self.db.execute(
            select(SessionRecording).where(SessionRecording.session_id == session_id).order_by(SessionRecording.created_at.desc())
        )
        return list(rows.scalars().all())

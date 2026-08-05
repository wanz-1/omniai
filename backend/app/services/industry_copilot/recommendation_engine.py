from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_copilot import CopilotRecommendation, CopilotAnalytic, CopilotSession
from app.services.ai_service import ai_service

class RecommendationEngine:
    def __init__(self, db: AsyncSession): self.db = db

    async def generate_recommendations(self, session_id, user_id, organization_id, industry, context=None):
        msgs = await self.db.execute(select(CopilotSession).where(CopilotSession.id == session_id))
        session = msgs.scalar_one_or_none()
        if not session: return []
        recs = await self.db.execute(select(CopilotRecommendation).where(CopilotRecommendation.session_id == session_id).order_by(CopilotRecommendation.created_at.desc()).limit(3))
        existing = list(recs.scalars().all())
        p = f"""Based on an industry {industry} copilot session, suggest 2-3 actionable recommendations.
Context: {context or {}}
Return numbered recommendations with title and description."""
        text = await ai_service.complete(p)
        rec = CopilotRecommendation(session_id=session_id, organization_id=organization_id, user_id=user_id, industry=industry, recommendation_type="suggestion", title="AI Recommendation", description=text, confidence=0.85)
        self.db.add(rec); await self.db.commit(); await self.db.refresh(rec)
        return existing + [rec]

    async def track_event(self, organization_id, copilot_id, user_id, event_type, details=None):
        a = CopilotAnalytic(organization_id=organization_id, copilot_id=copilot_id, user_id=user_id, event_type=event_type, details=details or {})
        self.db.add(a); await self.db.commit()

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_copilot import CopilotAnalytic, CopilotRecommendation, CopilotSession, CopilotWorkflowExecution

class CopilotAnalyticsService:
    def __init__(self, db: AsyncSession): self.db = db

    async def get_dashboard(self, organization_id):
        sessions = await self.db.execute(select(func.count(CopilotSession.id)).where(CopilotSession.organization_id == organization_id))
        total_sessions = sessions.scalar() or 0
        recs = await self.db.execute(select(func.count(CopilotRecommendation.id)).where(CopilotRecommendation.organization_id == organization_id))
        total_recommendations = recs.scalar() or 0
        wfs = await self.db.execute(select(func.count(CopilotWorkflowExecution.id)).where(CopilotWorkflowExecution.organization_id == organization_id))
        total_workflows = wfs.scalar() or 0
        events = await self.db.execute(select(CopilotAnalytic.event_type, func.count(CopilotAnalytic.id)).where(CopilotAnalytic.organization_id == organization_id).group_by(CopilotAnalytic.event_type))
        event_counts = {row[0]: row[1] for row in events.all()}
        return {"total_sessions": total_sessions, "total_recommendations": total_recommendations, "total_workflows_executed": total_workflows, "event_counts": event_counts}

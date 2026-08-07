from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_infrastructure import SecurityEvent
from app.services.ai_service import ai_service


class InfraSecurityManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(self, event_type, severity, description=None, source=None, details=None, ip_address=None, user_id=None, organization_id=None):
        event = SecurityEvent(
            event_type=event_type, severity=severity, description=description,
            source=source, details=details or {}, ip_address=ip_address,
            user_id=user_id, organization_id=organization_id,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def list_events(self, event_type=None, severity=None, resolved=None, limit=50):
        query = select(SecurityEvent)
        if event_type:
            query = query.where(SecurityEvent.event_type == event_type)
        if severity:
            query = query.where(SecurityEvent.severity == severity)
        if resolved is not None:
            query = query.where(SecurityEvent.is_resolved == resolved)
        query = query.order_by(SecurityEvent.created_at.desc()).limit(limit)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def resolve_event(self, event_id, action_taken=None):
        event = await self.db.get(SecurityEvent, event_id)
        if not event:
            return None
        event.is_resolved = True
        event.resolved_at = datetime.now(UTC)
        event.action_taken = action_taken
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def analyze_threat(self, description, context=None):
        ctx = context or {}
        prompt = f"""Analyze this security event and provide a risk assessment.

Event: {description}
Context: {ctx}

Return a JSON with: threat_level (low/medium/high/critical), recommended_action, and reasoning."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=500)
        return {"analysis": result.get("content", ""), "event": description}

    async def get_security_summary(self, organization_id=None):
        query = select(SecurityEvent)
        if organization_id:
            query = query.where(SecurityEvent.organization_id == organization_id)
        rows = (await self.db.execute(query)).scalars().all()
        return {
            "total_events": len(rows),
            "critical": sum(1 for e in rows if e.severity == "critical"),
            "high": sum(1 for e in rows if e.severity == "high"),
            "medium": sum(1 for e in rows if e.severity == "medium"),
            "low": sum(1 for e in rows if e.severity == "low"),
            "resolved": sum(1 for e in rows if e.is_resolved),
            "unresolved": sum(1 for e in rows if not e.is_resolved),
        }

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v6_governance import AIDecision, UserFeedback

logger = logging.getLogger("omniai.governance.audit")


class AIAuditService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    async def record_decision(
        self,
        user_id: str = "",
        organization_id: str = "",
        session_id: str = "",
        model: str = "",
        prompt_version: str = "",
        input_text: str = "",
        output_text: str = "",
        sources: list[str] | None = None,
        tools_used: list[str] | None = None,
        risk_level: str = "low",
        requires_review: bool = False,
        final_action: str = "completed",
        meta_data: dict[str, Any] | None = None,
    ) -> AIDecision:
        decision = AIDecision(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if user_id else None,
            organization_id=uuid.UUID(organization_id) if organization_id else None,
            session_id=session_id or None,
            model=model or "unknown",
            prompt_version=prompt_version or None,
            input_text=input_text[:10000],
            output_text=output_text[:10000],
            sources=sources or None,
            tools_used=tools_used or None,
            risk_level=risk_level,
            requires_review=requires_review,
            review_status="auto_approved" if not requires_review else "pending",
            final_action=final_action,
            meta_data=meta_data or None,
        )
        self.db.add(decision)
        await self.db.flush()

        logger.info(
            "AI decision recorded",
            extra={
                "decision_id": str(decision.id),
                "model": model,
                "risk_level": risk_level,
                "requires_review": requires_review,
            },
        )
        return decision

    async def get_decisions(
        self,
        user_id: str = "",
        model: str = "",
        limit: int = 50,
    ) -> list[AIDecision]:
        query = select(AIDecision).order_by(desc(AIDecision.created_at))
        if user_id:
            query = query.where(AIDecision.user_id == uuid.UUID(user_id))
        if model:
            query = query.where(AIDecision.model == model)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_decision(self, decision_id: str) -> AIDecision | None:
        result = await self.db.execute(
            select(AIDecision).where(AIDecision.id == uuid.UUID(decision_id))
        )
        return result.scalar_one_or_none()

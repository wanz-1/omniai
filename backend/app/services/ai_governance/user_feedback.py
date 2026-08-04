import uuid
import logging
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v6_governance import UserFeedback

logger = logging.getLogger("omniai.governance.feedback")


class UserFeedbackService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    async def submit_feedback(
        self,
        user_id: str,
        decision_id: str = "",
        model: str = "",
        rating: int = 1,
        rating_type: str = "thumbs",
        correction: str = "",
        comment: str = "",
        category: str = "",
        tags: list[str] | None = None,
    ) -> UserFeedback:
        feedback = UserFeedback(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if user_id else None,
            decision_id=uuid.UUID(decision_id) if decision_id else None,
            model=model or "unknown",
            rating=rating,
            rating_type=rating_type,
            correction=correction or None,
            comment=comment or None,
            category=category or None,
            tags=tags or None,
        )
        self.db.add(feedback)
        await self.db.flush()
        return feedback

    async def get_model_feedback_summary(self, model: str) -> dict[str, Any]:
        result = await self.db.execute(
            select(
                func.count(),
                func.avg(UserFeedback.rating),
            ).where(UserFeedback.model == model)
        )
        row = result.one()
        total = row[0] or 0
        avg_rating = float(row[1] or 0.0)

        result = await self.db.execute(
            select(func.count()).where(
                UserFeedback.model == model,
                UserFeedback.rating >= 4,
            )
        )
        positive = result.scalar() or 0

        return {
            "model": model,
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "positive_ratio": round(positive / max(total, 1) * 100, 2),
            "positive_count": positive,
        }

    async def get_feedback(self, model: str = "", limit: int = 50) -> list[UserFeedback]:
        query = select(UserFeedback).order_by(desc(UserFeedback.created_at))
        if model:
            query = query.where(UserFeedback.model == model)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

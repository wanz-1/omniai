import uuid
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v6_governance import HumanReview, AIDecision

logger = logging.getLogger("omniai.governance.approval")


class ApprovalWorkflowService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    def determine_risk_level(self, output_text: str, tools_used: list[str] | None = None) -> str:
        text_lower = output_text.lower()
        high_risk_keywords = [
            "financial", "legal", "compliance", "regulation", "audit",
            "contract", "agreement", "policy", "confidential", "classified",
            "patient", "health", "medical", "diagnosis", "prescription",
        ]
        destructive_tools = {"delete_document", "delete_resource", "execute_code", "run_sql_query"}

        if tools_used and any(t in destructive_tools for t in tools_used):
            return "high"

        high_count = sum(1 for kw in high_risk_keywords if kw in text_lower)
        if high_count >= 3:
            return "high"
        if high_count >= 1:
            return "medium"

        return "low"

    async def create_review_request(
        self,
        decision_id: str,
        reviewer_id: str,
        organization_id: str = "",
        risk_level: str = "medium",
        input_summary: str = "",
        output_summary: str = "",
        expires_hours: int = 72,
    ) -> HumanReview:
        review = HumanReview(
            id=uuid.uuid4(),
            decision_id=uuid.UUID(decision_id) if decision_id else None,
            reviewer_id=uuid.UUID(reviewer_id),
            organization_id=uuid.UUID(organization_id) if organization_id else None,
            status="pending",
            risk_level=risk_level,
            input_summary=input_summary[:500] or None,
            output_summary=output_summary[:500] or None,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        )
        self.db.add(review)
        await self.db.flush()

        if decision_id:
            result = await self.db.execute(
                select(AIDecision).where(AIDecision.id == uuid.UUID(decision_id))
            )
            decision = result.scalar_one_or_none()
            if decision:
                decision.requires_review = True
                decision.review_status = "pending"
                await self.db.flush()

        logger.info(
            "Review request created",
            extra={"review_id": str(review.id), "risk_level": risk_level, "reviewer_id": reviewer_id},
        )
        return review

    async def approve(self, review_id: str, comments: str = "") -> bool:
        result = await self.db.execute(
            select(HumanReview).where(HumanReview.id == uuid.UUID(review_id))
        )
        review = result.scalar_one_or_none()
        if not review or review.status != "pending":
            return False

        review.status = "approved"
        review.decision = "approve"
        review.comments = comments or None
        review.reviewed_at = datetime.now(timezone.utc)

        if review.decision_id:
            result2 = await self.db.execute(
                select(AIDecision).where(AIDecision.id == review.decision_id)
            )
            decision = result2.scalar_one_or_none()
            if decision:
                decision.review_status = "approved"
                decision.final_action = "completed"
        await self.db.flush()
        return True

    async def reject(self, review_id: str, comments: str = "") -> bool:
        result = await self.db.execute(
            select(HumanReview).where(HumanReview.id == uuid.UUID(review_id))
        )
        review = result.scalar_one_or_none()
        if not review or review.status != "pending":
            return False

        review.status = "rejected"
        review.decision = "reject"
        review.comments = comments or None
        review.reviewed_at = datetime.now(timezone.utc)

        if review.decision_id:
            result2 = await self.db.execute(
                select(AIDecision).where(AIDecision.id == review.decision_id)
            )
            decision = result2.scalar_one_or_none()
            if decision:
                decision.review_status = "rejected"
                decision.final_action = "blocked"
        await self.db.flush()
        return True

    async def list_pending(self, reviewer_id: str = "", limit: int = 50) -> list[HumanReview]:
        query = select(HumanReview).where(HumanReview.status == "pending").order_by(desc(HumanReview.created_at))
        if reviewer_id:
            query = query.where(HumanReview.reviewer_id == uuid.UUID(reviewer_id))
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

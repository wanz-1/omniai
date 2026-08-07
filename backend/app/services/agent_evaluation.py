import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_network import AgentPerformance, AgentReview
from app.services.ai_service import ai_service

EVALUATION_SYSTEM_PROMPT = """You are an AI agent evaluator. Review the output of AI agents and provide:
1. Quality score (0-10)
2. Accuracy assessment
3. Areas for improvement
4. Confidence level (0-1)
5. Specific suggestions

Be objective and constructive. Focus on factual accuracy, completeness, and clarity."""


class AgentEvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def review_output(
        self,
        reviewer_id: uuid.UUID,
        reviewee_id: uuid.UUID,
        content_to_review: str,
        task_id: uuid.UUID | None = None,
        criteria: dict | None = None,
    ) -> AgentReview:
        messages = [
            {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this AI agent output:\n\n{content_to_review}\n\nCriteria: {criteria or 'general quality'}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        review_content = result.get("content", "")
        score = await self._extract_score(review_content)
        confidence = await self._extract_confidence(review_content)

        review = AgentReview(
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            score=score,
            content=review_content,
            review_type="peer" if reviewer_id != reviewee_id else "self",
            criteria_scores=criteria,
            confidence=confidence,
            suggestions=self._extract_suggestions(review_content),
            is_approved=score >= 7.0,
            task_id=task_id,
        )
        self.db.add(review)
        await self._update_performance(reviewee_id)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def self_review(self, agent_id: uuid.UUID, output: str) -> AgentReview:
        return await self.review_output(agent_id, agent_id, output)

    async def get_agent_reviews(self, agent_id: uuid.UUID, limit: int = 20) -> list[AgentReview]:
        result = await self.db.execute(
            select(AgentReview)
            .where(AgentReview.reviewee_id == agent_id)
            .order_by(AgentReview.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_performance(self, agent_id: uuid.UUID) -> AgentPerformance | None:
        result = await self.db.execute(
            select(AgentPerformance).where(AgentPerformance.agent_id == agent_id)
        )
        return result.scalar_one_or_none()

    async def _update_performance(self, agent_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(AgentPerformance).where(AgentPerformance.agent_id == agent_id)
        )
        perf = result.scalar_one_or_none()

        reviews_result = await self.db.execute(
            select(func.avg(AgentReview.score), func.count(AgentReview.id))
            .where(AgentReview.reviewee_id == agent_id)
        )
        avg_score, review_count = reviews_result.one()

        if perf:
            perf.total_tasks += 1
            perf.avg_score = float(avg_score) if avg_score else perf.avg_score
        else:
            perf = AgentPerformance(
                agent_id=agent_id,
                total_tasks=1,
                avg_score=float(avg_score) if avg_score else None,
            )
            self.db.add(perf)

    async def _extract_score(self, content: str) -> float:
        import re
        scores = re.findall(r'(?:score|rating|quality)[:\s]+(\d+(?:\.\d+)?)', content.lower())
        if scores:
            return min(10.0, max(0.0, float(scores[0])))
        return 7.0

    async def _extract_confidence(self, content: str) -> float:
        import re
        confs = re.findall(r'confidence[:\s]+(\d+(?:\.\d+)?)', content.lower())
        if confs:
            return min(1.0, max(0.0, float(confs[0])))
        return 0.8

    def _extract_suggestions(self, content: str) -> list[str]:
        import re
        suggestions = re.findall(r'(?:suggestion|improvement|recommend)[:\s]*(.+?)(?:\n|$)', content, re.IGNORECASE)
        return [s.strip() for s in suggestions if s.strip()][:5]

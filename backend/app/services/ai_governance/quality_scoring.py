import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v6_governance import AIEvaluation, HallucinationEvent, QualityScore

logger = logging.getLogger("omniai.governance.quality")


class QualityScoringService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    def compute_overall_score(
        self,
        accuracy: float = 0.0,
        safety: float = 0.0,
        citation: float = 0.0,
        latency_ms: int = 0,
        tokens_used: int = 0,
    ) -> dict[str, float]:
        latency_score = self._compute_latency_score(latency_ms)
        cost_score = self._compute_cost_score(tokens_used)

        overall = (
            accuracy * 0.35 +
            safety * 0.30 +
            citation * 0.10 +
            latency_score * 0.15 +
            cost_score * 0.10
        )

        return {
            "overall": round(overall, 2),
            "accuracy": round(accuracy, 2),
            "safety": round(safety, 2),
            "citation": round(citation, 2),
            "latency": round(latency_score, 2),
            "cost_efficiency": round(cost_score, 2),
        }

    def _compute_latency_score(self, latency_ms: int) -> float:
        if latency_ms <= 500:
            return 100.0
        if latency_ms <= 1000:
            return 90.0
        if latency_ms <= 2000:
            return 75.0
        if latency_ms <= 5000:
            return 50.0
        return 25.0

    def _compute_cost_score(self, tokens_used: int) -> float:
        if tokens_used <= 100:
            return 100.0
        if tokens_used <= 500:
            return 90.0
        if tokens_used <= 2000:
            return 70.0
        if tokens_used <= 10000:
            return 40.0
        return 10.0

    async def generate_quality_report(self, model: str) -> dict[str, Any]:
        result = await self.db.execute(
            select(func.avg(AIEvaluation.accuracy_score), func.avg(AIEvaluation.safety_score))
            .where(AIEvaluation.model == model)
        )
        row = result.one()
        avg_accuracy = row[0] or 0.0
        avg_safety = row[1] or 0.0

        result = await self.db.execute(
            select(func.count()).where(
                AIEvaluation.model == model,
                AIEvaluation.passed == False,
            )
        )
        failed_count = result.scalar() or 0

        result = await self.db.execute(
            select(func.count()).where(AIEvaluation.model == model)
        )
        total_count = result.scalar() or 0

        scores = self.compute_overall_score(
            accuracy=avg_accuracy,
            safety=avg_safety,
        )

        return {
            "model": model,
            "total_evaluations": total_count,
            "failed_evaluations": failed_count,
            "pass_rate": round((total_count - failed_count) / max(total_count, 1) * 100, 2),
            "scores": scores,
        }

    async def save_quality_snapshot(
        self,
        model: str,
        period_hours: int = 24,
    ) -> QualityScore:
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(hours=period_hours)

        result = await self.db.execute(
            select(
                func.avg(AIEvaluation.accuracy_score),
                func.avg(AIEvaluation.safety_score),
                func.avg(AIEvaluation.citation_score),
                func.avg(AIEvaluation.latency_ms),
                func.sum(AIEvaluation.tokens_used),
                func.count(),
            ).where(
                AIEvaluation.model == model,
                AIEvaluation.created_at >= period_start,
            )
        )
        row = result.one()
        avg_accuracy = row[0] or 0.0
        avg_safety = row[1] or 0.0
        avg_citation = row[2] or 0.0
        avg_latency = row[3] or 0
        total_tokens = row[4] or 0
        total_count = row[5] or 0

        result = await self.db.execute(
            select(func.count()).where(
                HallucinationEvent.model == model,
                HallucinationEvent.created_at >= period_start,
            )
        )
        h_count = result.scalar() or 0

        scores = self.compute_overall_score(
            accuracy=avg_accuracy,
            safety=avg_safety,
            citation=avg_citation or 0,
            latency_ms=avg_latency or 0,
        )

        snapshot = QualityScore(
            id=uuid.uuid4(),
            model=model,
            period_start=period_start,
            period_end=now,
            overall_score=scores["overall"],
            accuracy_score=scores["accuracy"],
            safety_score=scores["safety"],
            citation_score=scores.get("citation", 0),
            latency_score=scores["latency"],
            cost_efficiency_score=scores.get("cost_efficiency", 0),
            total_evaluations=total_count,
            hallucination_rate=round(h_count / max(total_count, 1) * 100, 2),
            avg_latency_ms=round(avg_latency) if avg_latency else None,
            total_tokens=total_tokens,
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_quality_history(self, model: str, limit: int = 30) -> list[QualityScore]:
        result = await self.db.execute(
            select(QualityScore)
            .where(QualityScore.model == model)
            .order_by(desc(QualityScore.period_start))
            .limit(limit)
        )
        return list(result.scalars().all())

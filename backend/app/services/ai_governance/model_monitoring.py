import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v6_governance import ModelMetric

logger = logging.getLogger("omniai.governance.model_monitoring")


class ModelMonitoringService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    async def record_request(
        self,
        model: str,
        provider: str,
        success: bool,
        latency_ms: int,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        cost: float = 0.0,
        quality_score: float | None = None,
    ) -> None:
        now = datetime.now(UTC)
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.db.execute(
            select(ModelMetric).where(
                ModelMetric.model == model,
                ModelMetric.period_start == period_start,
            )
        )
        metric = result.scalar_one_or_none()

        if not metric:
            metric = ModelMetric(
                id=uuid.uuid4(),
                model=model,
                provider=provider,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                total_cost=0.0,
                period_start=period_start,
                period_end=period_start + timedelta(days=1),
            )
            self.db.add(metric)

        metric.total_requests += 1
        if success:
            metric.successful_requests += 1
        else:
            metric.failed_requests += 1
        metric.total_tokens += tokens_prompt + tokens_completion
        metric.prompt_tokens += tokens_prompt
        metric.completion_tokens += tokens_completion
        metric.total_cost += cost

        if metric.avg_latency_ms:
            metric.avg_latency_ms = (metric.avg_latency_ms * (metric.total_requests - 1) + latency_ms) / metric.total_requests
        else:
            metric.avg_latency_ms = float(latency_ms)

        if quality_score is not None:
            if metric.avg_quality_score:
                metric.avg_quality_score = (metric.avg_quality_score * (metric.total_requests - 1) + quality_score) / metric.total_requests
            else:
                metric.avg_quality_score = quality_score

        await self.db.flush()

    async def get_model_metrics(
        self,
        model: str = "",
        limit: int = 20,
    ) -> list[ModelMetric]:
        query = select(ModelMetric).order_by(desc(ModelMetric.period_start))
        if model:
            query = query.where(ModelMetric.model == model)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_model_summary(self) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(
                ModelMetric.model,
                func.sum(ModelMetric.total_requests),
                func.sum(ModelMetric.successful_requests),
                func.sum(ModelMetric.failed_requests),
                func.sum(ModelMetric.total_tokens),
                func.sum(ModelMetric.total_cost),
                func.avg(ModelMetric.avg_latency_ms),
                func.avg(ModelMetric.avg_quality_score),
            ).group_by(ModelMetric.model)
        )
        summaries: list[dict[str, Any]] = []
        for row in result.all():
            summaries.append({
                "model": row[0],
                "total_requests": row[1] or 0,
                "successful_requests": row[2] or 0,
                "failed_requests": row[3] or 0,
                "total_tokens": row[4] or 0,
                "total_cost": round(row[5] or 0, 4),
                "avg_latency_ms": round(row[6] or 0, 2),
                "avg_quality_score": round(row[7] or 0, 2) if row[7] else None,
            })
        return summaries

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_infrastructure import (
    AIModelRegistry, ClusterDeployment, MonitoringMetric, ServiceDeployment,
)
from app.services.ai_service import ai_service


class InfraScalingEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_model(self, name, provider, model_id, model_type, capabilities=None, cost=0.0, latency_p50=0.0, latency_p99=0.0, max_tokens=4096):
        model = AIModelRegistry(
            name=name, provider=provider, model_id=model_id, model_type=model_type,
            capabilities=capabilities or [], cost_per_token=cost, latency_p50=latency_p50,
            latency_p99=latency_p99, max_tokens=max_tokens,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def list_models(self, model_type=None, provider=None):
        query = select(AIModelRegistry)
        if model_type:
            query = query.where(AIModelRegistry.model_type == model_type)
        if provider:
            query = query.where(AIModelRegistry.provider == provider)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def route_model(self, task, complexity="medium", max_cost=None, preferred_provider=None, required_capabilities=None):
        query = select(AIModelRegistry).where(AIModelRegistry.is_active == True)
        if preferred_provider:
            query = query.where(AIModelRegistry.provider == preferred_provider)
        rows = await self.db.execute(query)
        models = list(rows.scalars().all())

        if not models:
            return {"model_id": "gpt-4o", "provider": "openai", "name": "GPT-4o", "cost": 0.0, "latency": 0.0, "reason": "default"}

        scored = []
        for m in models:
            score = 0
            if required_capabilities and m.capabilities:
                match = sum(1 for c in required_capabilities if c in m.capabilities)
                score += match * 10
            if complexity == "simple":
                score += (100 - m.cost_per_token * 1000)
                score += (100 - m.latency_p50)
            elif complexity == "complex":
                score += m.max_tokens / 100
                score += (100 if "reasoning" in (m.capabilities or []) else 0)
            else:
                score += (50 - m.cost_per_token * 500)
                score += (50 - m.latency_p50 / 2)
            if max_cost and m.cost_per_token > max_cost:
                score -= 1000
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]

        return {
            "model_id": best.model_id, "provider": best.provider,
            "name": best.name, "cost": best.cost_per_token,
            "latency": best.latency_p50, "reason": f"Best match (score: {scored[0][0]:.0f})",
        }

    async def get_cluster_utilization(self):
        rows = await self.db.execute(
            select(MonitoringMetric)
            .where(MonitoringMetric.metric_type == "resource")
            .order_by(MonitoringMetric.recorded_at.desc())
            .limit(20)
        )
        return list(rows.scalars().all())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_simulation import SimulationRecommendation
from app.services.ai_service import ai_service

class OptimizationEngine:
    def __init__(self, db: AsyncSession): self.db = db

    async def optimize(self, organization_id, objective, constraints, variables):
        prompt = f"""Solve this resource optimization problem.
Objective: {objective}
Constraints: {constraints}
Variables to optimize: {variables}
Provide: optimal solution, resource allocation, trade-offs, expected outcome, confidence level."""
        result = await ai_service.complete(prompt)
        rec = SimulationRecommendation(organization_id=organization_id, title="Resource Optimization", description=result, recommendation_type="optimization", expected_impact="High", confidence=0.85)
        self.db.add(rec); await self.db.commit(); await self.db.refresh(rec); return rec

    async def allocate_resources(self, organization_id, activities, total_budget):
        prompt = f"""Allocate budget of ${total_budget} across these activities:
{activities}
Provide: optimal allocation per activity, rationale, expected ROI, risk level."""
        result = await ai_service.complete(prompt)
        rec = SimulationRecommendation(organization_id=organization_id, title="Budget Allocation", description=result, recommendation_type="optimization", expected_impact="Medium", confidence=0.80)
        self.db.add(rec); await self.db.commit(); await self.db.refresh(rec); return rec

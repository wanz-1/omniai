from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_simulation import Simulation, Scenario, RiskAssessment, SimulationRecommendation

class SimulationAnalytics:
    def __init__(self, db: AsyncSession): self.db = db

    async def get_dashboard(self, organization_id):
        sims = await self.db.execute(select(func.count(Simulation.id)).where(Simulation.organization_id == organization_id))
        scens = await self.db.execute(select(func.count(Scenario.id)).where(Scenario.organization_id == organization_id))
        risks = await self.db.execute(select(func.count(RiskAssessment.id)).where(RiskAssessment.organization_id == organization_id))
        recs = await self.db.execute(select(func.count(SimulationRecommendation.id)).where(SimulationRecommendation.organization_id == organization_id))
        by_type = await self.db.execute(select(Simulation.simulation_type, func.count(Simulation.id)).where(Simulation.organization_id == organization_id).group_by(Simulation.simulation_type))
        return {"total_simulations": sims.scalar() or 0, "total_scenarios": scens.scalar() or 0, "total_risks": risks.scalar() or 0, "total_recommendations": recs.scalar() or 0, "by_type": {row[0]: row[1] for row in by_type.all()}}

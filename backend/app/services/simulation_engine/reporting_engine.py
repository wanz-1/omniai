from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_simulation import SimulationReport, Simulation, SimulationOutcome, Prediction, RiskAssessment, SimulationRecommendation
from app.services.ai_service import ai_service

class ReportingEngine:
    def __init__(self, db: AsyncSession): self.db = db

    async def generate_report(self, simulation_id, report_type, title=None):
        sim = await self.db.get(Simulation, simulation_id)
        if not sim: return None
        outcomes = await self.db.execute(select(SimulationOutcome).where(SimulationOutcome.simulation_id == simulation_id))
        predictions = await self.db.execute(select(Prediction).where(Prediction.simulation_id == simulation_id))
        risks = await self.db.execute(select(RiskAssessment).where(RiskAssessment.simulation_id == simulation_id))
        recs = await self.db.execute(select(SimulationRecommendation).where(SimulationRecommendation.simulation_id == simulation_id))
        prompt = f"""Generate a {report_type} simulation report.
Simulation: {sim.title if hasattr(sim, 'title') else sim.id}
Type: {sim.simulation_type}
Output: {sim.output_data}
Outcomes: {[str(o.id) for o in outcomes.scalars().all()]}
Predictions: {[str(p.id) for p in predictions.scalars().all()]}
Risks: {[str(r.id) for r in risks.scalars().all()]}
Recommendations: {[str(r.id) for r in recs.scalars().all()]}
Create a comprehensive report with: executive summary, methodology, findings, recommendations, appendices."""
        content = await ai_service.complete(prompt)
        report = SimulationReport(simulation_id=simulation_id, organization_id=sim.organization_id, title=title or f"Simulation Report - {sim.simulation_type}", report_type=report_type, content={"report": content})
        self.db.add(report); await self.db.commit(); await self.db.refresh(report); return report

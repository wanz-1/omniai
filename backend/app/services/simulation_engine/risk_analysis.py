from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_simulation import RiskAssessment, SimulationOutcome, Simulation
from app.services.ai_service import ai_service
from datetime import datetime, timezone

class RiskAnalysis:
    def __init__(self, db: AsyncSession): self.db = db

    async def analyze_risks(self, simulation_id, organization_id, context=None):
        sim = await self.db.get(Simulation, simulation_id)
        prompt = f"""Perform a comprehensive risk analysis.
Context: {context or 'General business scenario'}
Simulation data: {sim.output_data if sim else 'N/A'}
Identify risks in these categories:
1. Financial (budget overruns, funding gaps, cost increases)
2. Operational (resource shortages, delays, process failures)
3. Compliance (policy violations, missing documentation)
4. Technical (system failures, security issues)
For each risk provide: name, description, probability (0-1), impact (0-1), risk score, mitigation strategy."""
        result = await ai_service.complete(prompt)
        ra = RiskAssessment(simulation_id=simulation_id, organization_id=organization_id, category="comprehensive", risk_name="AI Risk Assessment", description=result, probability=0.7, impact=0.7, risk_score=0.49, status="open")
        self.db.add(ra); await self.db.commit(); await self.db.refresh(ra); return ra

    async def calculate_risk_score(self, probability, impact):
        return probability * impact

    async def get_risk_matrix(self, organization_id):
        rows = await self.db.execute(select(RiskAssessment).where(RiskAssessment.organization_id == organization_id))
        risks = list(rows.scalars().all())
        matrix = {"critical": [], "high": [], "medium": [], "low": []}
        for r in risks:
            if r.risk_score >= 0.7: matrix["critical"].append(r)
            elif r.risk_score >= 0.5: matrix["high"].append(r)
            elif r.risk_score >= 0.3: matrix["medium"].append(r)
            else: matrix["low"].append(r)
        return matrix

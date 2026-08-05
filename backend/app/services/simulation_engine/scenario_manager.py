from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_simulation import Scenario, SimulationVariable, Simulation
from app.services.ai_service import ai_service
from datetime import datetime, timezone

class ScenarioManager:
    def __init__(self, db: AsyncSession): self.db = db

    async def create_scenario(self, organization_id, name, description, scenario_type, twin_id=None, base_state=None, variables=None, assumptions=None, created_by=None):
        sc = Scenario(organization_id=organization_id, name=name, description=description, scenario_type=scenario_type, twin_id=twin_id, base_state=base_state or {}, variables=variables or [], assumptions=assumptions or [], created_by=created_by or organization_id)
        self.db.add(sc); await self.db.commit(); await self.db.refresh(sc)
        if variables:
            for v in variables:
                sv = SimulationVariable(scenario_id=sc.id, name=v.get("name"), variable_type=v.get("variable_type", "budget"), current_value=v.get("current_value", 0), simulated_value=v.get("simulated_value"), unit=v.get("unit", ""))
                self.db.add(sv)
            await self.db.commit()
        return sc

    async def run_simulation(self, scenario_id, simulation_type, user_id=None):
        sc = await self.db.get(Scenario, scenario_id)
        if not sc: return None
        org_id = sc.organization_id
        sim = Simulation(organization_id=org_id, scenario_id=scenario_id, user_id=user_id or org_id, status="running", simulation_type=simulation_type, input_snapshot={"scenario": sc.name, "type": sc.scenario_type, "variables": sc.variables}, started_at=datetime.now(timezone.utc))
        self.db.add(sim); await self.db.commit(); await self.db.refresh(sim)
        prompt = f"""Run a {simulation_type} simulation for scenario: {sc.name}
Description: {sc.description}
Type: {sc.scenario_type}
Base state: {sc.base_state}
Variables: {sc.variables}
Assumptions: {sc.assumptions}
Provide: outcome analysis, key predictions, risk assessment, recommendations, confidence level."""
        result = await ai_service.complete(prompt)
        sim.output_data = {"result": result}
        sim.status = "completed"; sim.completed_at = datetime.now(timezone.utc)
        await self.db.commit(); await self.db.refresh(sim)
        return sim

    async def compare_scenarios(self, scenario_ids):
        scenarios = []
        for sid in scenario_ids:
            sc = await self.db.get(Scenario, sid)
            if sc: scenarios.append(sc)
        names = "\n".join([f"- {s.name} ({s.scenario_type}): {s.description}" for s in scenarios])
        prompt = f"""Compare these scenarios and recommend the best option:
{names}
Provide: comparison table, pros/cons, risk analysis, recommendation with confidence score."""
        result = await ai_service.complete(prompt)
        return {"comparison": result, "scenarios": [{"id": str(s.id), "name": s.name, "type": s.scenario_type} for s in scenarios]}

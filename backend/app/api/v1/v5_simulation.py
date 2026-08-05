import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v5_simulation import (
    DigitalTwinResponse, DigitalTwinEntityResponse, ScenarioResponse,
    SimulationResponse, PredictionResponse, RiskAssessmentResponse,
    SimulationReportResponse,
    CreateScenarioRequest, RunSimulationRequest, CompareScenariosRequest,
    CreateDigitalTwinRequest, AddEntityRequest, OptimizationRequest,
)
from app.services.simulation_engine.scenario_manager import ScenarioManager
from app.services.simulation_engine.forecasting_engine import ForecastingEngine
from app.services.simulation_engine.risk_analysis import RiskAnalysis
from app.services.simulation_engine.optimization_engine import OptimizationEngine
from app.services.simulation_engine.financial_modeling import FinancialModeling
from app.services.simulation_engine.project_simulation import ProjectSimulation
from app.services.simulation_engine.digital_twin_service import DigitalTwinService
from app.services.simulation_engine.reporting_engine import ReportingEngine
from app.services.simulation_engine.simulation_analytics import SimulationAnalytics

router = APIRouter()


@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(req: CreateScenarioRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = ScenarioManager(db)
    return await mgr.create_scenario(current_user.organization_id or current_user.id, req.name, req.description, req.scenario_type, req.twin_id, req.base_state, req.variables, req.assumptions, current_user.id)


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(scenario_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.v5_simulation import Scenario
    q = select(Scenario).where(Scenario.organization_id == (current_user.organization_id or current_user.id))
    if scenario_type: q = q.where(Scenario.scenario_type == scenario_type)
    q = q.order_by(Scenario.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


@router.post("/simulations/run", response_model=SimulationResponse)
async def run_simulation(req: RunSimulationRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = ScenarioManager(db)
    return await mgr.run_simulation(req.scenario_id, req.simulation_type, current_user.id)


@router.get("/simulations/{simulation_id}/results")
async def get_simulation_results(simulation_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.v5_simulation import Simulation
    sim = await db.get(Simulation, simulation_id)
    if not sim: return {"error": "not_found"}
    return {"id": str(sim.id), "status": sim.status, "output_data": sim.output_data, "started_at": sim.started_at.isoformat() if sim.started_at else None, "completed_at": sim.completed_at.isoformat() if sim.completed_at else None}


@router.get("/simulations", response_model=list[SimulationResponse])
async def list_simulations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.v5_simulation import Simulation
    rows = await db.execute(select(Simulation).where(Simulation.organization_id == (current_user.organization_id or current_user.id)).order_by(Simulation.started_at.desc()))
    return list(rows.scalars().all())


@router.post("/scenarios/compare")
async def compare_scenarios(req: CompareScenariosRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = ScenarioManager(db)
    return await mgr.compare_scenarios(req.scenario_ids)


@router.post("/digital-twins", response_model=DigitalTwinResponse)
async def create_digital_twin(req: CreateDigitalTwinRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DigitalTwinService(db)
    return await svc.create_twin(current_user.organization_id or current_user.id, req.name, req.description, req.twin_type, req.config, current_user.id)


@router.get("/digital-twins", response_model=list[DigitalTwinResponse])
async def list_digital_twins(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DigitalTwinService(db)
    return await svc.list_twins(current_user.organization_id or current_user.id)


@router.post("/digital-twins/{twin_id}/entities", response_model=DigitalTwinEntityResponse)
async def add_twin_entity(twin_id: uuid.UUID, req: AddEntityRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DigitalTwinService(db)
    return await svc.add_entity(twin_id, req.entity_type, req.name, req.attributes)


@router.get("/digital-twins/{twin_id}/entities", response_model=list[DigitalTwinEntityResponse])
async def get_twin_entities(twin_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DigitalTwinService(db)
    return await svc.get_twin_entities(twin_id)


@router.post("/digital-twins/{twin_id}/analyze")
async def analyze_twin(twin_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DigitalTwinService(db)
    result = await svc.analyze_twin(twin_id)
    return {"analysis": result}


@router.post("/financial/budget-scenario")
async def budget_scenario(current_budget: float, scenario_description: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FinancialModeling(db)
    result = await svc.budget_scenario(current_user.organization_id or current_user.id, current_budget, scenario_description)
    return {"result": result}


@router.post("/financial/cashflow")
async def cashflow_projection(inflows: str, outflows: str, period_months: int = 12, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FinancialModeling(db)
    result = await svc.cashflow_projection(current_user.organization_id or current_user.id, inflows, outflows, period_months)
    return {"result": result}


@router.post("/financial/revenue-forecast")
async def revenue_forecast(historical_revenue: str, growth_assumptions: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FinancialModeling(db)
    result = await svc.revenue_forecast(current_user.organization_id or current_user.id, historical_revenue, growth_assumptions)
    return {"result": result}


@router.post("/financial/cost-impact")
async def cost_impact_analysis(current_costs: str, change_scenario: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = FinancialModeling(db)
    result = await svc.cost_impact_analysis(current_user.organization_id or current_user.id, current_costs, change_scenario)
    return {"result": result}


@router.post("/project/simulate")
async def simulate_project(project_data: str, scenario: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ProjectSimulation(db)
    result = await svc.simulate_project(current_user.organization_id or current_user.id, project_data, scenario)
    return {"result": result}


@router.post("/project/resource-impact")
async def resource_impact(project_data: str, resource_change: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ProjectSimulation(db)
    result = await svc.resource_impact(current_user.organization_id or current_user.id, project_data, resource_change)
    return {"result": result}


@router.post("/project/timeline-what-if")
async def timeline_what_if(project_plan: str, delay_scenario: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ProjectSimulation(db)
    result = await svc.timeline_what_if(current_user.organization_id or current_user.id, project_plan, delay_scenario)
    return {"result": result}


@router.post("/risks/analyze", response_model=RiskAssessmentResponse)
async def analyze_risks(simulation_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = RiskAnalysis(db)
    return await svc.analyze_risks(simulation_id, current_user.organization_id or current_user.id)


@router.get("/risks/matrix")
async def get_risk_matrix(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = RiskAnalysis(db)
    return await svc.get_risk_matrix(current_user.organization_id or current_user.id)


@router.post("/optimize")
async def optimize_resources(req: OptimizationRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = OptimizationEngine(db)
    return await svc.optimize(current_user.organization_id or current_user.id, req.objective, req.constraints, req.variables)


@router.post("/forecast", response_model=PredictionResponse)
async def forecast(simulation_id: uuid.UUID, metric_name: str, prediction_type: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ForecastingEngine(db)
    return await svc.forecast(current_user.organization_id or current_user.id, simulation_id, metric_name, prediction_type)


@router.post("/reports/generate", response_model=SimulationReportResponse)
async def generate_report(simulation_id: uuid.UUID, report_type: str = "summary", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ReportingEngine(db)
    return await svc.generate_report(simulation_id, report_type)


@router.get("/analytics/dashboard")
async def simulation_analytics_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = SimulationAnalytics(db)
    return await svc.get_dashboard(current_user.organization_id or current_user.id)

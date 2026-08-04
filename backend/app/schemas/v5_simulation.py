import uuid
from datetime import datetime
from pydantic import BaseModel


class DigitalTwinResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; name: str
    description: str | None = None; twin_type: str
    config: dict | None = None; is_active: bool = True
    created_by: uuid.UUID; last_synced_at: datetime | None = None
    class Config: from_attributes = True


class DigitalTwinEntityResponse(BaseModel):
    id: uuid.UUID; twin_id: uuid.UUID; entity_type: str; name: str
    attributes: dict | None = None; relationships: list | None = None
    is_active: bool = True
    class Config: from_attributes = True


class SimulationModelResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; name: str
    description: str | None = None; model_type: str
    config: dict | None = None; is_template: bool = False
    created_by: uuid.UUID
    class Config: from_attributes = True


class ScenarioResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID
    twin_id: uuid.UUID | None = None; model_id: uuid.UUID | None = None
    name: str; description: str | None = None; scenario_type: str
    base_state: dict | None = None; variables: list | None = None
    assumptions: list | None = None; created_by: uuid.UUID
    class Config: from_attributes = True


class SimulationResponse(BaseModel):
    id: uuid.UUID; organization_id: uuid.UUID; scenario_id: uuid.UUID
    user_id: uuid.UUID; status: str; simulation_type: str
    input_snapshot: dict | None = None; output_data: dict | None = None
    started_at: datetime | None = None; completed_at: datetime | None = None
    error: str | None = None
    class Config: from_attributes = True


class SimulationVariableResponse(BaseModel):
    id: uuid.UUID; scenario_id: uuid.UUID; name: str; variable_type: str
    current_value: float; simulated_value: float | None = None
    unit: str; min_range: float | None = None; max_range: float | None = None
    description: str | None = None
    class Config: from_attributes = True


class PredictionResponse(BaseModel):
    id: uuid.UUID; simulation_id: uuid.UUID; organization_id: uuid.UUID
    prediction_type: str; metric_name: str; predicted_value: float
    confidence: float; lower_bound: float | None = None
    upper_bound: float | None = None; time_period: str
    details: dict | None = None
    class Config: from_attributes = True


class SimulationOutcomeResponse(BaseModel):
    id: uuid.UUID; simulation_id: uuid.UUID; scenario_id: uuid.UUID
    outcome_type: str; description: str | None = None; severity: str
    probability: float; impact_value: float | None = None
    details: dict | None = None
    class Config: from_attributes = True


class RiskAssessmentResponse(BaseModel):
    id: uuid.UUID; simulation_id: uuid.UUID; organization_id: uuid.UUID
    category: str; risk_name: str; description: str | None = None
    probability: float; impact: float; risk_score: float
    mitigation: str | None = None; status: str
    class Config: from_attributes = True


class SimulationRecommendationResponse(BaseModel):
    id: uuid.UUID; simulation_id: uuid.UUID; organization_id: uuid.UUID
    title: str; description: str | None = None; recommendation_type: str
    expected_impact: str; confidence: float
    alternatives: list | None = None; is_applied: bool = False
    class Config: from_attributes = True


class SimulationReportResponse(BaseModel):
    id: uuid.UUID; simulation_id: uuid.UUID; organization_id: uuid.UUID
    title: str; report_type: str; content: dict | None = None
    generated_by: uuid.UUID; generated_at: datetime | None = None
    class Config: from_attributes = True


class CreateScenarioRequest(BaseModel):
    name: str
    description: str
    scenario_type: str
    twin_id: uuid.UUID | None = None
    base_state: dict | None = None
    variables: list | None = None
    assumptions: list | None = None


class RunSimulationRequest(BaseModel):
    scenario_id: uuid.UUID
    simulation_type: str


class CompareScenariosRequest(BaseModel):
    scenario_ids: list[uuid.UUID]


class CreateDigitalTwinRequest(BaseModel):
    name: str
    description: str
    twin_type: str
    config: dict | None = None


class AddEntityRequest(BaseModel):
    twin_id: uuid.UUID
    entity_type: str
    name: str
    attributes: dict | None = None


class OptimizationRequest(BaseModel):
    objective: str
    constraints: dict
    variables: list


class SimulationQuery(BaseModel):
    query: str
    context: dict | None = None

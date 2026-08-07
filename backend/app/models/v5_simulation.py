import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class DigitalTwin(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "digital_twins"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    twin_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="digital_twins")
    entities = relationship("DigitalTwinEntity", back_populates="twin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"DigitalTwin(id={self.id}, name={self.name}, type={self.twin_type})"


class DigitalTwinEntity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "digital_twin_entities"

    twin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("digital_twins.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    attributes: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    relationships: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    twin = relationship("DigitalTwin", back_populates="entities")

    def __repr__(self):
        return f"DigitalTwinEntity(id={self.id}, name={self.name}, type={self.entity_type})"


class SimulationModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_models"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    def __repr__(self):
        return f"SimulationModel(id={self.id}, name={self.name}, type={self.model_type})"


class Scenario(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scenarios"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    twin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("digital_twins.id"), nullable=True, index=True)
    model_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("simulation_models.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    base_state: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    variables: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    assumptions: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    def __repr__(self):
        return f"Scenario(id={self.id}, name={self.name}, type={self.scenario_type})"


class Simulation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulations"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    simulation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    predictions = relationship("Prediction", back_populates="simulation", cascade="all, delete-orphan")
    outcomes = relationship("SimulationOutcome", back_populates="simulation", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="simulation", cascade="all, delete-orphan")
    recommendations = relationship("SimulationRecommendation", back_populates="simulation", cascade="all, delete-orphan")
    reports = relationship("SimulationReport", back_populates="simulation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Simulation(id={self.id}, status={self.status}, type={self.simulation_type})"


class SimulationVariable(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_variables"

    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    variable_type: Mapped[str] = mapped_column(String(50), nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    simulated_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    min_range: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_range: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"SimulationVariable(id={self.id}, name={self.name}, type={self.variable_type})"


class Prediction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "predictions"

    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_period: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    simulation = relationship("Simulation", back_populates="predictions")

    def __repr__(self):
        return f"Prediction(id={self.id}, metric={self.metric_name}, value={self.predicted_value})"


class SimulationOutcome(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_outcomes"

    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False, index=True)
    scenario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False, index=True)
    outcome_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    impact_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    simulation = relationship("Simulation", back_populates="outcomes")

    def __repr__(self):
        return f"SimulationOutcome(id={self.id}, type={self.outcome_type}, severity={self.severity})"


class RiskAssessment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "risk_assessments"

    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    impact: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)

    simulation = relationship("Simulation", back_populates="risk_assessments")

    def __repr__(self):
        return f"RiskAssessment(id={self.id}, risk={self.risk_name}, score={self.risk_score})"


class SimulationRecommendation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_recommendations"

    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_impact: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    alternatives: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    simulation = relationship("Simulation", back_populates="recommendations")

    def __repr__(self):
        return f"SimulationRecommendation(id={self.id}, title={self.title}, type={self.recommendation_type})"


class SimulationReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_reports"

    simulation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    generated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    simulation = relationship("Simulation", back_populates="reports")

    def __repr__(self):
        return f"SimulationReport(id={self.id}, title={self.title}, type={self.report_type})"

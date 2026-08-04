from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_simulation import Prediction, Simulation
from app.services.ai_service import ai_service

class ForecastingEngine:
    def __init__(self, db: AsyncSession): self.db = db

    async def forecast(self, organization_id, simulation_id, metric_name, prediction_type, historical_data=None):
        sim = await self.db.get(Simulation, simulation_id)
        prompt = f"""Generate a {prediction_type} forecast for {metric_name}.
Historical data: {historical_data or 'Not provided'}
Simulation context: {sim.output_data if sim else 'N/A'}
Provide: predicted value, confidence interval (lower/upper), confidence percentage, timeframe, key drivers."""
        result = await ai_service.complete(prompt)
        p = Prediction(simulation_id=simulation_id, organization_id=organization_id, prediction_type=prediction_type, metric_name=metric_name, predicted_value=0.0, confidence=0.85, details={"forecast": result})
        self.db.add(p); await self.db.commit(); await self.db.refresh(p); return p

    async def multi_year_forecast(self, organization_id, simulation_id, base_value, growth_rate=0.05, years=5):
        sim = await self.db.get(Simulation, simulation_id)
        projections = []
        val = base_value
        for y in range(1, years + 1):
            val *= (1 + growth_rate)
            projections.append({"year": y, "projected_value": round(val, 2)})
        prompt = f"""Analyze this {years}-year financial projection: {projections}
Base value: {base_value}, Growth rate: {growth_rate}
Provide: trend analysis, risks, opportunities, recommendations."""
        analysis = await ai_service.complete(prompt)
        p = Prediction(simulation_id=simulation_id, organization_id=organization_id, prediction_type="multi_year", metric_name="financial_projection", predicted_value=val, confidence=0.80, details={"projections": projections, "analysis": analysis})
        self.db.add(p); await self.db.commit(); await self.db.refresh(p); return p

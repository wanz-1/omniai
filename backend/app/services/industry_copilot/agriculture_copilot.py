from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_service import ai_service

class AgricultureCopilot:
    def __init__(self, db: AsyncSession): self.db = db

    async def plan_farming(self, farm_data):
        p = f"""Create a farm plan.
Farm data: {farm_data}
Provide: crop selection, planting schedule, resource requirements, expected yield, risk factors."""
        return await ai_service.complete(p)

    async def analyze_costs(self, cost_data):
        p = f"""Analyze farming costs: {cost_data}
Provide: cost breakdown, profitability analysis, optimization opportunities, breakeven analysis."""
        return await ai_service.complete(p)

    async def market_insights(self, crop_type, region):
        p = f"""Provide market insights.
Crop: {crop_type}, Region: {region}
Include: current prices, demand trends, seasonal patterns, export opportunities, price forecasts."""
        return await ai_service.complete(p)

    async def generate_training(self, topic, audience):
        p = f"""Create training material.
Topic: {topic}, Audience: {audience}
Include: learning objectives, key concepts, practical exercises, visual aids suggestions, assessment."""
        return await ai_service.complete(p)

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_service import ai_service

class HospitalityCopilot:
    def __init__(self, db: AsyncSession): self.db = db

    async def analyze_occupancy(self, occupancy_data):
        p = f"""Analyze hotel occupancy data: {occupancy_data}
Provide: occupancy trends, peak periods, pricing recommendations, revenue optimization, competitive insights."""
        return await ai_service.complete(p)

    async def generate_marketing(self, campaign_type, property_info):
        p = f"""Generate {campaign_type} marketing content.
Property: {property_info}
Create: campaign ideas, social media posts, email content, target audience suggestions."""
        return await ai_service.complete(p)

    async def analyze_feedback(self, feedback_data):
        p = f"""Analyze guest feedback: {feedback_data}
Provide: sentiment analysis, common themes, actionable improvements, priority recommendations."""
        return await ai_service.complete(p)

    async def optimize_pricing(self, property_data, market_data):
        p = f"""Optimize pricing strategy.
Property: {property_data}
Market: {market_data}
Provide: recommended rates, dynamic pricing suggestions, seasonal adjustments, package ideas."""
        return await ai_service.complete(p)

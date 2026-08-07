from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import ai_service


class BusinessCopilot:
    def __init__(self, db: AsyncSession): self.db = db

    async def analyze_strategy(self, company_data, market_data):
        p = f"""Analyze business strategy.
Company: {company_data}
Market: {market_data}
Provide: SWOT analysis, competitive positioning, growth opportunities, strategic recommendations, risk assessment."""
        return await ai_service.complete(p)

    async def analyze_kpis(self, kpi_data):
        p = f"""Analyze KPIs: {kpi_data}
Provide: performance overview, trends, benchmarks, improvement areas, action items."""
        return await ai_service.complete(p)

    async def analyze_sales(self, sales_data):
        p = f"""Analyze sales data: {sales_data}
Provide: sales trends, top performers, pipeline analysis, conversion optimization, revenue forecasts."""
        return await ai_service.complete(p)

    async def customer_insights(self, customer_data):
        p = f"""Analyze customer data: {customer_data}
Provide: segmentation, satisfaction analysis, churn risk, upsell opportunities, engagement recommendations."""
        return await ai_service.complete(p)

    async def process_improvement(self, process_description):
        p = f"""Analyze and improve this business process:
{process_description}
Provide: process analysis, bottlenecks, automation opportunities, optimization suggestions, expected impact."""
        return await ai_service.complete(p)

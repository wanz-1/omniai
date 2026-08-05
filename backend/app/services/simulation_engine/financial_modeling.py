from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_service import ai_service

class FinancialModeling:
    def __init__(self, db: AsyncSession): self.db = db

    async def budget_scenario(self, organization_id, current_budget, scenario_description):
        prompt = f"""Analyze this budget scenario:
Current budget: ${current_budget}
Scenario: {scenario_description}
Calculate: new projected budget, line-item impact, risk level, recommended actions, contingency plan."""
        return await ai_service.complete(prompt)

    async def cashflow_projection(self, organization_id, inflows, outflows, period_months=12):
        prompt = f"""Generate cash flow projection.
Monthly inflows: {inflows}
Monthly outflows: {outflows}
Period: {period_months} months
Provide: monthly projections, net position, peak deficit, surplus periods, recommendations.
Calculate: operating cash flow, free cash flow, burn rate, runway."""
        return await ai_service.complete(prompt)

    async def revenue_forecast(self, organization_id, historical_revenue, growth_assumptions):
        prompt = f"""Generate revenue forecast.
Historical revenue: {historical_revenue}
Growth assumptions: {growth_assumptions}
Provide: revenue projections, growth rates, seasonal patterns, confidence intervals, key drivers."""
        return await ai_service.complete(prompt)

    async def cost_impact_analysis(self, organization_id, current_costs, change_scenario):
        prompt = f"""Analyze cost impact.
Current costs: {current_costs}
Change scenario: {change_scenario}
Calculate: new cost structure, affected categories, savings/overruns, breakeven analysis, recommendations."""
        return await ai_service.complete(prompt)

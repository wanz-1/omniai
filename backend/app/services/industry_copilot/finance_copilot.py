from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_service import ai_service

class FinanceCopilot:
    def __init__(self, db: AsyncSession): self.db = db

    async def analyze_budget(self, budget_data):
        p = f"""Analyze this budget data: {budget_data}
Provide: variance analysis, anomalies, optimization opportunities, category breakdown, recommendations."""
        return await ai_service.complete(p)

    async def forecast(self, historical_data, period):
        p = f"""Create a financial forecast.
Historical data: {historical_data}
Period: {period}
Provide: projected revenue, expenses, cash flow, key assumptions, risks."""
        return await ai_service.complete(p)

    async def generate_report(self, report_type, data):
        p = f"""Generate a {report_type} report.
Data: {data}
Include: executive summary, financial highlights, variance analysis, KPIs, recommendations."""
        return await ai_service.complete(p)

    async def detect_anomalies(self, transactions):
        p = f"""Analyze these financial transactions for anomalies.
Transactions: {transactions}
Flag: duplicates, unusual amounts, policy violations, suspicious patterns."""
        return await ai_service.complete(p)

    async def analyze_cashflow(self, cashflow_data):
        p = f"""Analyze cash flow: {cashflow_data}
Provide: inflows/outflows analysis, burn rate, runway, working capital, improvement suggestions."""
        return await ai_service.complete(p)

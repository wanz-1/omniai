import uuid
from pydantic import BaseModel


class UsageSummaryResponse(BaseModel):
    total_api_calls: int = 0
    total_tokens: int = 0
    total_credits_used: int = 0
    total_duration_ms: int = 0
    average_duration_ms: float = 0
    success_rate: float = 0
    calls_by_model: dict = {}
    calls_by_action: dict = {}
    calls_by_day: dict = {}


class AgentPerformanceResponse(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_duration_ms: float = 0
    total_tokens: int = 0
    satisfaction_score: float = 0


class RevenueSummaryResponse(BaseModel):
    total_revenue: float = 0
    mrr: float = 0
    arr: float = 0
    active_subscriptions: int = 0
    revenue_by_plan: dict = {}
    revenue_by_day: dict = {}
    recent_transactions: list = []


class GrowthMetricsResponse(BaseModel):
    total_users: int = 0
    new_users_7d: int = 0
    total_orgs: int = 0
    new_orgs_7d: int = 0
    user_growth_rate: float = 0
    org_growth_rate: float = 0
    retention_rate: float = 0

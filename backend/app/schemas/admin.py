import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SystemOverviewResponse(BaseModel):
    total_users: int = 0
    total_organizations: int = 0
    total_projects: int = 0
    total_agents: int = 0
    total_api_calls: int = 0
    total_storage_mb: float = 0
    active_users_24h: int = 0
    active_users_7d: int = 0
    revenue_mtd: float = 0
    new_users_today: int = 0
    new_orgs_today: int = 0


class DailyUsageResponse(BaseModel):
    date: str
    api_calls: int = 0
    active_users: int = 0
    tokens_used: int = 0
    credits_used: int = 0
    revenue: float = 0


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    role: str
    two_factor_enabled: bool
    credits_balance: int = 0
    created_at: datetime | None = None
    last_login_at: datetime | None = None
    organization_count: int = 0
    project_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminSystemSettings(BaseModel):
    allow_registration: bool = True
    require_email_verification: bool = True
    default_credits: int = 100
    max_upload_size_mb: int = 50
    maintenance_mode: bool = False
    maintenance_message: str | None = None
    rate_limit_per_minute: int = 60
    allowed_origins: list[str] | None = None

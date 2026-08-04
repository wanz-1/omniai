import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class SubscriptionPlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    price_monthly: Decimal
    price_yearly: Decimal
    currency: str = "USD"
    credits_monthly: int = 0
    max_users: int = 1
    max_projects: int = 5
    max_agents: int = 1
    max_api_requests: int = 1000
    max_storage_mb: int = 100
    features: list | None = None
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    plan_id: uuid.UUID
    status: str
    interval: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    trial_end: datetime | None = None
    cancelled_at: datetime | None = None
    plan: SubscriptionPlanResponse | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    plan_id: uuid.UUID
    interval: str = "monthly"
    organization_id: uuid.UUID
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    url: str
    session_id: str


class BillingPortalRequest(BaseModel):
    organization_id: uuid.UUID
    return_url: str


class BillingPortalResponse(BaseModel):
    url: str


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    subscription_id: uuid.UUID | None = None
    amount: Decimal
    currency: str
    status: str
    paid_at: datetime | None = None
    due_date: datetime | None = None
    lines: list | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True

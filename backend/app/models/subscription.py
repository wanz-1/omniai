import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SubscriptionStatus, SubscriptionInterval
from app.models.base import Base, TimestampMixin, UUIDMixin


class SubscriptionPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subscription_plans"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_monthly: Mapped[Decimal] = mapped_column(Float, default=0, nullable=False)
    price_yearly: Mapped[Decimal] = mapped_column(Float, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    credits_monthly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_users: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_projects: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_agents: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_api_requests: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_storage_mb: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    features: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(String(255), nullable=True)

    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self) -> str:
        return f"SubscriptionPlan(id={self.id}, name={self.name}, price={self.price_monthly})"


class Subscription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False
    )
    interval: Mapped[SubscriptionInterval] = mapped_column(
        Enum(SubscriptionInterval), default=SubscriptionInterval.MONTHLY, nullable=False
    )
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    organization = relationship("Organization", back_populates="subscription")

    def __repr__(self) -> str:
        return f"Subscription(id={self.id}, status={self.status}, plan={self.plan_id})"


class Invoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoices"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lines: Mapped[dict | None] = mapped_column(JSONB, default=list, nullable=True)

    def __repr__(self) -> str:
        return f"Invoice(id={self.id}, amount={self.amount}, status={self.status})"

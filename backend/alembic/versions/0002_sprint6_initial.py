"""Sprint 6: Subscription, marketplace, integration models

Revision ID: 0002
Revises: (base)
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User Sessions
    op.create_table(
        "user_sessions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(255), nullable=False, index=True),
        sa.Column("refresh_token_hash", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("device_name", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Subscription Plans
    op.create_table(
        "subscription_plans",
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("price_monthly", sa.Float, default=0, nullable=False),
        sa.Column("price_yearly", sa.Float, default=0, nullable=False),
        sa.Column("currency", sa.String(3), default="USD", nullable=False),
        sa.Column("credits_monthly", sa.Integer, default=0, nullable=False),
        sa.Column("max_users", sa.Integer, default=1, nullable=False),
        sa.Column("max_projects", sa.Integer, default=5, nullable=False),
        sa.Column("max_agents", sa.Integer, default=1, nullable=False),
        sa.Column("max_api_requests", sa.Integer, default=1000, nullable=False),
        sa.Column("max_storage_mb", sa.Integer, default=100, nullable=False),
        sa.Column("features", postgresql.JSONB, default=list),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("sort_order", sa.Integer, default=0, nullable=False),
        sa.Column("stripe_price_id_monthly", sa.String(255), nullable=True),
        sa.Column("stripe_price_id_yearly", sa.String(255), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("status", sa.Enum("active", "past_due", "canceled", "incomplete", "trialing", "expired", name="subscriptionstatus"), default="active", nullable=False),
        sa.Column("interval", sa.Enum("monthly", "yearly", name="subscriptioninterval"), default="monthly", nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB, default=dict),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Invoices
    op.create_table(
        "invoices",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(3), default="USD", nullable=False),
        sa.Column("status", sa.String(20), default="pending", nullable=False),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lines", postgresql.JSONB, default=list),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Integration Connections
    op.create_table(
        "integration_connections",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config", postgresql.JSONB, default=dict),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Marketplace Items
    op.create_table(
        "marketplace_items",
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("item_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="draft", nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("short_description", sa.String(300), nullable=True),
        sa.Column("category", sa.String(100), nullable=True, index=True),
        sa.Column("tags", postgresql.JSONB, default=list),
        sa.Column("price", sa.Float, default=0, nullable=False),
        sa.Column("currency", sa.String(3), default="USD", nullable=False),
        sa.Column("preview_image_url", sa.Text, nullable=True),
        sa.Column("demo_url", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.String(20), default="1.0.0", nullable=False),
        sa.Column("downloads", sa.Integer, default=0, nullable=False),
        sa.Column("rating", sa.Float, nullable=True),
        sa.Column("rating_count", sa.Integer, default=0, nullable=False),
        sa.Column("config", postgresql.JSONB, default=dict),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Marketplace Purchases
    op.create_table(
        "marketplace_purchases",
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_items.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("amount", sa.Float, default=0, nullable=False),
        sa.Column("currency", sa.String(3), default="USD", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("marketplace_purchases")
    op.drop_table("marketplace_items")
    op.drop_table("integration_connections")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("user_sessions")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
    op.execute("DROP TYPE IF EXISTS subscriptioninterval")

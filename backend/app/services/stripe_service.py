import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import SubscriptionInterval, SubscriptionStatus
from app.core.exceptions import AppError
from app.models.organization import Organization
from app.models.subscription import Invoice, Subscription, SubscriptionPlan

try:
    import stripe
    stripe.api_key = settings.stripe_secret_key
    STRIPE_AVAILABLE = bool(settings.stripe_secret_key)
except Exception:
    STRIPE_AVAILABLE = False


async def create_stripe_checkout_session(
    plan: SubscriptionPlan,
    organization_id: uuid.UUID,
    interval: str,
    success_url: str,
    cancel_url: str,
    customer_email: str | None = None,
) -> dict:
    if not STRIPE_AVAILABLE:
        return create_mock_checkout(plan, organization_id, interval)

    price_id = plan.stripe_price_id_monthly if interval == "monthly" else plan.stripe_price_id_yearly
    if not price_id:
        raise AppError(detail=f"No Stripe price ID configured for plan '{plan.name}' ({interval})")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        client_reference_id=str(organization_id),
        customer_email=customer_email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"organization_id": str(organization_id), "plan_id": str(plan.id), "interval": interval},
    )
    return {"url": session.url, "session_id": session.id}


async def create_stripe_portal_session(organization_id: uuid.UUID, return_url: str) -> dict:
    if not STRIPE_AVAILABLE:
        return {"url": return_url}

    sub_result = await _get_db_session().execute(
        select(Subscription).where(Subscription.organization_id == organization_id)
    )
    sub = sub_result.scalar_one_or_none()
    if not sub or not sub.stripe_customer_id:
        raise AppError(detail="No Stripe customer found for this organization")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=return_url,
    )
    return {"url": session.url}


async def handle_stripe_webhook(payload: bytes, sig_header: str) -> dict:
    if not STRIPE_AVAILABLE:
        return {"received": True}

    event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    handlers = {
        "checkout.session.completed": handle_checkout_completed,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_invoice_failed,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
    }
    handler = handlers.get(event_type)
    if handler:
        await handler(data)
    return {"received": True}


async def handle_checkout_completed(session_data: dict):
    metadata = session_data.get("metadata", {})
    org_id = metadata.get("organization_id")
    plan_id = metadata.get("plan_id")
    interval = metadata.get("interval", "monthly")
    customer_id = session_data.get("customer")
    sub_id = session_data.get("subscription")

    if not all([org_id, plan_id, sub_id]):
        return

    async with _session() as db:
        existing = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
        )
        sub = existing.scalar_one_or_none()
        if sub:
            sub.plan_id = uuid.UUID(plan_id)
            sub.interval = interval
            sub.stripe_customer_id = customer_id
            sub.status = SubscriptionStatus.ACTIVE
        else:
            sub = Subscription(
                organization_id=uuid.UUID(org_id),
                plan_id=uuid.UUID(plan_id),
                interval=interval,
                stripe_subscription_id=sub_id,
                stripe_customer_id=customer_id,
                status=SubscriptionStatus.ACTIVE,
            )
            db.add(sub)
        await db.flush()
        await db.commit()


async def handle_invoice_paid(invoice_data: dict):
    stripe_sub_id = invoice_data.get("subscription")
    stripe_invoice_id = invoice_data.get("id")
    amount_paid = invoice_data.get("amount_paid")
    currency = invoice_data.get("currency", "usd")

    if not stripe_sub_id:
        return

    async with _session() as db:
        sub_result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = sub_result.scalar_one_or_none()
        if not sub:
            return

        sub.status = SubscriptionStatus.ACTIVE
        period_start = invoice_data.get("period_start") or invoice_data.get("created")
        period_end = invoice_data.get("period_end")
        if isinstance(period_start, (int, float)):
            sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
        if isinstance(period_end, (int, float)):
            sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

        existing_inv = await db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        )
        invoice = existing_inv.scalar_one_or_none()
        if not invoice and amount_paid is not None:
            invoice = Invoice(
                organization_id=sub.organization_id,
                subscription_id=sub.id,
                amount=Decimal(str(amount_paid)) / 100,
                currency=currency.upper(),
                status="paid",
                stripe_invoice_id=stripe_invoice_id,
                paid_at=datetime.now(timezone.utc),
            )
            db.add(invoice)
        elif invoice and amount_paid is not None:
            invoice.status = "paid"
            invoice.paid_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()


async def handle_invoice_failed(invoice_data: dict):
    stripe_sub_id = invoice_data.get("subscription")
    if not stripe_sub_id:
        return

    async with _session() as db:
        sub_result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = sub_result.scalar_one_or_none()
        if not sub:
            return
        sub.status = SubscriptionStatus.PAST_DUE
        await db.flush()
        await db.commit()


async def handle_subscription_updated(sub_data: dict):
    stripe_sub_id = sub_data.get("id")
    if not stripe_sub_id:
        return

    interval = "monthly"
    for item in sub_data.get("items", {}).get("data", []):
        for price in item.get("prices", []):
            if price.get("interval"):
                interval = price["interval"]
                break
        else:
            plan = item.get("plan") or {}
            if plan.get("interval"):
                interval = plan["interval"]

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.PAST_DUE,
        "trialing": SubscriptionStatus.ACTIVE,
    }

    async with _session() as db:
        sub_result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = sub_result.scalar_one_or_none()
        if not sub:
            return
        new_status = status_map.get(sub_data.get("status", ""))
        if new_status:
            sub.status = new_status
        if interval in (SubscriptionInterval.MONTHLY, SubscriptionInterval.YEARLY):
            sub.interval = interval
        period_start = sub_data.get("current_period_start")
        period_end = sub_data.get("current_period_end")
        if isinstance(period_start, (int, float)):
            sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
        if isinstance(period_end, (int, float)):
            sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
        await db.flush()
        await db.commit()


async def handle_subscription_deleted(sub_data: dict):
    stripe_sub_id = sub_data.get("id")
    if not stripe_sub_id:
        return

    async with _session() as db:
        sub_result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = sub_result.scalar_one_or_none()
        if not sub:
            return
        sub.status = SubscriptionStatus.CANCELED
        sub.cancelled_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()


def create_mock_checkout(plan: SubscriptionPlan, organization_id: uuid.UUID, interval: str) -> dict:
    return {
        "url": f"/billing/confirm?plan_id={plan.id}&org_id={organization_id}&interval={interval}",
        "session_id": f"mock_{uuid.uuid4()}",
    }


async def sync_plan_from_stripe(plan_id: str) -> dict | None:
    if not STRIPE_AVAILABLE:
        return None
    try:
        price = stripe.Price.retrieve(plan_id)
        product = stripe.Product.retrieve(price.product)
        return {"price": price, "product": product}
    except Exception:
        return None


def _session() -> AsyncSession:
    from app.main import async_session_factory
    import contextlib
    return contextlib.asynccontextmanager(lambda: async_session_factory())

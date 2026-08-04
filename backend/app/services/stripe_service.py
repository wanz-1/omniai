import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.organization import Organization
from app.models.subscription import Subscription, SubscriptionPlan

try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    STRIPE_AVAILABLE = bool(settings.STRIPE_SECRET_KEY)
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
        meta_data={"organization_id": str(organization_id), "plan_id": str(plan.id), "interval": interval},
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

    db = _get_db_session()
    sub = Subscription(
        organization_id=uuid.UUID(org_id),
        plan_id=uuid.UUID(plan_id),
        interval=interval,
        stripe_subscription_id=sub_id,
        stripe_customer_id=customer_id,
        status="active",
    )
    db.add(sub)
    await db.flush()


async def handle_invoice_paid(invoice_data: dict):
    pass


async def handle_invoice_failed(invoice_data: dict):
    pass


async def handle_subscription_updated(sub_data: dict):
    pass


async def handle_subscription_deleted(sub_data: dict):
    pass


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


def _get_db_session() -> AsyncSession:
    from app.main import async_session_factory
    import contextlib
    return contextlib.asynccontextmanager(lambda: async_session_factory())()

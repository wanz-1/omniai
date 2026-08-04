import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SubscriptionInterval
from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.organization import Organization, OrganizationMember
from app.models.subscription import Subscription, SubscriptionPlan, Invoice
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.subscription import (
    BillingPortalRequest,
    BillingPortalResponse,
    CheckoutRequest,
    CheckoutResponse,
    InvoiceResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from app.services import stripe_service

router = APIRouter()


@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def list_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.sort_order)
    )
    return result.scalars().all()


@router.get("/subscriptions/{organization_id}", response_model=SubscriptionResponse)
async def get_subscription(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Subscription).where(Subscription.organization_id == organization_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise NotFoundError("Subscription", str(organization_id))

    plan_result = await db.get(SubscriptionPlan, sub.plan_id)
    sub.plan = plan_result
    return sub


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plan = await db.get(SubscriptionPlan, body.plan_id)
    if not plan:
        raise NotFoundError("SubscriptionPlan", str(body.plan_id))

    org = await db.get(Organization, body.organization_id)
    if not org:
        raise NotFoundError("Organization", str(body.organization_id))

    result = await stripe_service.create_stripe_checkout_session(
        plan=plan,
        organization_id=body.organization_id,
        interval=body.interval,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        customer_email=current_user.email,
    )
    return CheckoutResponse(url=result["url"], session_id=result["session_id"])


@router.post("/portal", response_model=BillingPortalResponse)
async def billing_portal(
    body: BillingPortalRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await stripe_service.create_stripe_portal_session(
        organization_id=body.organization_id,
        return_url=body.return_url,
    )
    return BillingPortalResponse(url=result["url"])


@router.get("/invoices/{organization_id}", response_model=list[InvoiceResponse])
async def list_invoices(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Invoice)
        .where(Invoice.organization_id == organization_id)
        .order_by(Invoice.created_at.desc())
    )
    return result.scalars().all()


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    return await stripe_service.handle_stripe_webhook(payload, sig_header)


@router.post("/subscriptions/{subscription_id}/cancel", response_model=MessageResponse)
async def cancel_subscription(
    subscription_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sub = await db.get(Subscription, subscription_id)
    if not sub:
        raise NotFoundError("Subscription", str(subscription_id))
    sub.status = "canceled"
    await db.flush()
    return MessageResponse(message="Subscription canceled successfully")

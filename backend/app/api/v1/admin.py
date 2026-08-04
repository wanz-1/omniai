import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.audit import AuditLog
from app.models.organization import Organization, OrganizationMember
from app.models.project import Project
from app.models.agent import AgentProfile
from app.models.subscription import SubscriptionPlan, Subscription, Invoice
from app.models.usage import UsageLog
from app.models.user import User
from app.models.marketplace import MarketplaceItem
from app.schemas.admin import (
    AdminSystemSettings,
    AdminUserResponse,
    DailyUsageResponse,
    SystemOverviewResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.marketplace import MarketplaceItemResponse

router = APIRouter()


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_superuser and current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    return current_user


@router.get("/overview", response_model=SystemOverviewResponse)
async def admin_overview(
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_orgs = (await db.execute(select(func.count(Organization.id)))).scalar() or 0
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    total_agents = (await db.execute(select(func.count(AgentProfile.id)))).scalar() or 0
    total_api_calls = (await db.execute(select(func.count(UsageLog.id)))).scalar() or 0

    active_24h = (await db.execute(
        select(func.count(User.id)).where(User.last_login_at >= now - timedelta(hours=24))
    )).scalar() or 0

    active_7d = (await db.execute(
        select(func.count(User.id)).where(User.last_login_at >= now - timedelta(days=7))
    )).scalar() or 0

    new_users_today = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )).scalar() or 0

    new_orgs_today = (await db.execute(
        select(func.count(Organization.id)).where(Organization.created_at >= today_start)
    )).scalar() or 0

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0))
        .where(
            and_(Invoice.status == "paid", Invoice.paid_at >= today_start - timedelta(days=30))
        )
    )
    revenue_mtd = float(revenue_result.scalar() or 0)

    return SystemOverviewResponse(
        total_users=total_users,
        total_organizations=total_orgs,
        total_projects=total_projects,
        total_agents=total_agents,
        total_api_calls=total_api_calls,
        active_users_24h=active_24h,
        active_users_7d=active_7d,
        revenue_mtd=revenue_mtd,
        new_users_today=new_users_today,
        new_orgs_today=new_orgs_today,
    )


@router.get("/users", response_model=list[AdminUserResponse])
async def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(User)
    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | User.display_name.ilike(f"%{search}%")
        )
    query = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    responses = []
    for user in users:
        org_count = (await db.execute(
            select(func.count(OrganizationMember.id)).where(OrganizationMember.user_id == user.id)
        )).scalar() or 0
        project_count = (await db.execute(
            select(func.count(Project.id)).where(Project.user_id == user.id)
        )).scalar() or 0
        responses.append(
            AdminUserResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_superuser=user.is_superuser,
                role=user.role,
                two_factor_enabled=user.two_factor_enabled,
                credits_balance=user.credits_balance,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                organization_count=org_count,
                project_count=project_count,
            )
        )
    return responses


@router.put("/users/{user_id}/suspend", response_model=MessageResponse)
async def suspend_user(
    user_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User", str(user_id))
    user.is_active = False
    await db.flush()
    return MessageResponse(message=f"User {user.display_name} has been suspended")


@router.put("/users/{user_id}/restore", response_model=MessageResponse)
async def restore_user(
    user_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User", str(user_id))
    user.is_active = True
    await db.flush()
    return MessageResponse(message=f"User {user.display_name} has been restored")


@router.get("/usage/daily", response_model=list[DailyUsageResponse])
async def admin_daily_usage(
    days: int = Query(30, ge=1, le=365),
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(UsageLog.created_at).label("date"),
            func.count(UsageLog.id).label("api_calls"),
            func.coalesce(func.sum(UsageLog.tokens_used), 0).label("tokens_used"),
            func.coalesce(func.sum(UsageLog.credits_used), 0).label("credits_used"),
        )
        .where(UsageLog.created_at >= start_date)
        .group_by(func.date(UsageLog.created_at))
        .order_by(func.date(UsageLog.created_at))
    )
    return [
        DailyUsageResponse(date=str(row.date), api_calls=row.api_calls, tokens_used=row.tokens_used, credits_used=row.credits_used)
        for row in result.all()
    ]


@router.get("/marketplace/items", response_model=list[MarketplaceItemResponse])
async def admin_marketplace_items(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(MarketplaceItem)
    if status:
        query = query.where(MarketplaceItem.status == status)
    query = query.order_by(MarketplaceItem.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    responses = []
    for item in items:
        user = await db.get(User, item.author_id)
        responses.append(
            MarketplaceItemResponse(
                **{c.name: getattr(item, c.name) for c in item.__table__.columns},
                author_name=user.display_name if user else None,
            )
        )
    return responses


@router.put("/marketplace/items/{item_id}/approve", response_model=MessageResponse)
async def approve_marketplace_item(
    item_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(MarketplaceItem, item_id)
    if not item:
        raise NotFoundError("MarketplaceItem", str(item_id))
    item.status = "approved"
    await db.flush()
    return MessageResponse(message=f"Item '{item.name}' has been approved")


@router.put("/marketplace/items/{item_id}/reject", response_model=MessageResponse)
async def reject_marketplace_item(
    item_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(MarketplaceItem, item_id)
    if not item:
        raise NotFoundError("MarketplaceItem", str(item_id))
    item.status = "rejected"
    await db.flush()
    return MessageResponse(message=f"Item '{item.name}' has been rejected")


@router.get("/audit-logs")
async def admin_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: Annotated[User, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    total = await db.execute(select(func.count(AuditLog.id)))
    return {
        "items": result.scalars().all(),
        "total": total.scalar() or 0,
        "page": page,
        "limit": limit,
    }


@router.get("/settings", response_model=AdminSystemSettings)
async def get_settings(
    admin: Annotated[User, Depends(require_admin)] = None,
):
    return AdminSystemSettings()


@router.put("/settings", response_model=AdminSystemSettings)
async def update_settings(
    body: AdminSystemSettings,
    admin: Annotated[User, Depends(require_admin)] = None,
):
    return body

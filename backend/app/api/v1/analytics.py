from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.agent import AgentProfile, AgentAnalytics
from app.models.organization import Organization, OrganizationMember
from app.models.subscription import Invoice, Subscription
from app.models.usage import UsageLog
from app.models.user import User
from app.schemas.analytics import (
    AgentPerformanceResponse,
    GrowthMetricsResponse,
    RevenueSummaryResponse,
    UsageSummaryResponse,
)

router = APIRouter()


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    logs_result = await db.execute(
        select(UsageLog).where(
            and_(UsageLog.user_id == current_user.id, UsageLog.created_at >= start)
        )
    )
    logs = logs_result.scalars().all()

    total_calls = len(logs)
    total_tokens = sum((l.tokens_used or 0) for l in logs)
    total_credits = sum((l.credits_used or 0) for l in logs)
    total_duration = sum((l.duration_ms or 0) for l in logs)
    successful = sum(1 for l in logs if l.success)
    avg_duration = total_duration / total_calls if total_calls else 0
    success_rate = (successful / total_calls * 100) if total_calls else 0

    models: dict = {}
    actions: dict = {}
    days_map: dict = {}
    for log in logs:
        model = log.model or "unknown"
        models[model] = models.get(model, 0) + 1
        action = log.action
        actions[action] = actions.get(action, 0) + 1
        day = log.created_at.strftime("%Y-%m-%d") if log.created_at else "unknown"
        days_map[day] = days_map.get(day, 0) + 1

    return UsageSummaryResponse(
        total_api_calls=total_calls,
        total_tokens=total_tokens,
        total_credits_used=total_credits,
        total_duration_ms=total_duration,
        average_duration_ms=round(avg_duration, 2),
        success_rate=round(success_rate, 2),
        calls_by_model=models,
        calls_by_action=actions,
        calls_by_day=days_map,
    )


@router.get("/agents", response_model=list[AgentPerformanceResponse])
async def agent_performance(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(AgentProfile).where(AgentProfile.user_id == current_user.id)
    )
    agents = result.scalars().all()

    responses = []
    for agent in agents:
        analytics = await db.execute(
            select(AgentAnalytics).where(AgentAnalytics.agent_id == agent.id)
        )
        a = analytics.scalar_one_or_none()
        responses.append(
            AgentPerformanceResponse(
                agent_id=agent.id,
                agent_name=agent.name,
                total_tasks=a.total_tasks if a else 0,
                completed_tasks=a.completed_tasks if a else 0,
                failed_tasks=a.failed_tasks if a else 0,
                avg_duration_ms=a.avg_duration_ms if a else 0,
                total_tokens=a.total_tokens if a else 0,
                satisfaction_score=a.avg_satisfaction if a else 0,
            )
        )
    return responses


@router.get("/revenue", response_model=RevenueSummaryResponse)
async def revenue_analytics(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    now = datetime.now(timezone.utc)
    month_start = now.replace(hour=0, minute=0, second=0, microsecond=0, day=1)

    org_ids_result = await db.execute(
        select(OrganizationMember.organization_id).where(OrganizationMember.user_id == current_user.id)
    )
    org_ids = [row[0] for row in org_ids_result.all()]

    invoices_result = await db.execute(
        select(Invoice).where(
            and_(Invoice.organization_id.in_(org_ids), Invoice.status == "paid")
        )
    )
    invoices = invoices_result.scalars().all()

    total_revenue = sum(float(i.amount) for i in invoices)
    mtd_revenue = sum(float(i.amount) for i in invoices if i.paid_at and i.paid_at >= month_start)

    active_subs = await db.execute(
        select(func.count(Subscription.id)).where(
            and_(Subscription.organization_id.in_(org_ids), Subscription.status == "active")
        )
    )

    return RevenueSummaryResponse(
        total_revenue=total_revenue,
        mrr=mtd_revenue,
        arr=mtd_revenue * 12,
        active_subscriptions=active_subs.scalar() or 0,
    )


@router.get("/growth", response_model=GrowthMetricsResponse)
async def growth_analytics(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_orgs = (await db.execute(select(func.count(Organization.id)))).scalar() or 0
    new_users = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= seven_days_ago)
    )).scalar() or 0
    new_orgs = (await db.execute(
        select(func.count(Organization.id)).where(Organization.created_at >= seven_days_ago)
    )).scalar() or 0

    return GrowthMetricsResponse(
        total_users=total_users,
        new_users_7d=new_users,
        total_orgs=total_orgs,
        new_orgs_7d=new_orgs,
        user_growth_rate=round((new_users / max(total_users, 1)) * 100, 2),
        org_growth_rate=round((new_orgs / max(total_orgs, 1)) * 100, 2),
    )

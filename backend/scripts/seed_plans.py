"""Seed subscription plans for Sprint 6."""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import OrganizationPlan
from app.models.subscription import SubscriptionPlan


PLANS = [
    {
        "name": "Free",
        "slug": "free",
        "description": "Get started with basic AI tools and limited usage.",
        "price_monthly": 0,
        "price_yearly": 0,
        "credits_monthly": 100,
        "max_users": 1,
        "max_projects": 3,
        "max_agents": 1,
        "max_api_requests": 500,
        "max_storage_mb": 50,
        "sort_order": 0,
        "features": [
            "100 AI credits/month",
            "Basic document tools",
            "1 AI agent",
            "Basic chatbot",
            "3 projects",
            "50 MB storage",
        ],
    },
    {
        "name": "Professional",
        "slug": "pro",
        "description": "For professionals who need more AI power and advanced tools.",
        "price_monthly": 29,
        "price_yearly": 290,
        "credits_monthly": 1000,
        "max_users": 1,
        "max_projects": 20,
        "max_agents": 5,
        "max_api_requests": 10000,
        "max_storage_mb": 500,
        "sort_order": 1,
        "features": [
            "1,000 AI credits/month",
            "Advanced document tools",
            "5 AI agents",
            "Website builder",
            "20 projects",
            "500 MB storage",
            "API access",
            "Priority support",
        ],
    },
    {
        "name": "Business",
        "slug": "business",
        "description": "For teams that need collaboration, higher limits, and integrations.",
        "price_monthly": 99,
        "price_yearly": 990,
        "credits_monthly": 5000,
        "max_users": 10,
        "max_projects": 100,
        "max_agents": 25,
        "max_api_requests": 100000,
        "max_storage_mb": 5000,
        "sort_order": 2,
        "features": [
            "5,000 AI credits/month",
            "Team collaboration",
            "25 AI agents",
            "All integrations",
            "100 projects",
            "5 GB storage",
            "Unlimited API access",
            "Priority support",
            "Custom workflows",
        ],
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "description": "For organizations needing self-hosting, SSO, and dedicated support.",
        "price_monthly": 499,
        "price_yearly": 4990,
        "credits_monthly": 50000,
        "max_users": 9999,
        "max_projects": 9999,
        "max_agents": 9999,
        "max_api_requests": 9999999,
        "max_storage_mb": 50000,
        "sort_order": 3,
        "features": [
            "50,000 AI credits/month",
            "Self-hosting option",
            "Unlimited agents",
            "Unlimited projects",
            "50 GB storage",
            "SSO / SAML",
            "Custom AI models",
            "Dedicated support",
            "SLA guarantee",
            "Custom integrations",
        ],
    },
]


async def seed_plans(db: AsyncSession) -> list[SubscriptionPlan]:
    created = []
    for plan_data in PLANS:
        existing = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_data["slug"])
        )
        if not existing.scalar_one_or_none():
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            created.append(plan)
    await db.flush()
    print(f"Seeded {len(created)} subscription plans")
    return created


async def main():
    from app.main import async_session_factory
    async with async_session_factory() as session:
        await seed_plans(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())

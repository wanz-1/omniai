from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.industry_solutions import Industry, SolutionPackage
from app.services.ai_service import ai_service


class IndustrySolutionBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_industries(self):
        rows = await self.db.execute(select(Industry).order_by(Industry.sort_order))
        return list(rows.scalars().all())

    async def get_industry(self, slug: str):
        rows = await self.db.execute(select(Industry).where(Industry.slug == slug))
        return rows.scalar_one_or_none()

    async def create_industry(self, name, slug, description=None, icon=None, color=None, config=None):
        industry = Industry(name=name, slug=slug, description=description, icon=icon, color=color, config=config or {})
        self.db.add(industry)
        await self.db.commit()
        await self.db.refresh(industry)
        return industry

    async def get_packages(self, industry_id):
        rows = await self.db.execute(
            select(SolutionPackage).where(SolutionPackage.industry_id == industry_id)
        )
        return list(rows.scalars().all())

    async def create_package(self, industry_id, name, description=None, capabilities=None):
        slug = name.lower().replace(" ", "-")
        pkg = SolutionPackage(
            industry_id=industry_id, name=name, slug=slug,
            description=description, capabilities=capabilities or [],
        )
        self.db.add(pkg)
        await self.db.commit()
        await self.db.refresh(pkg)
        return pkg

    async def install_package(self, package_id):
        pkg = await self.db.get(SolutionPackage, package_id)
        if not pkg:
            return None
        pkg.is_installed = True
        pkg.installed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(pkg)
        return pkg

    async def uninstall_package(self, package_id):
        pkg = await self.db.get(SolutionPackage, package_id)
        if not pkg:
            return None
        pkg.is_installed = False
        pkg.installed_at = None
        await self.db.commit()
        return pkg

    async def generate_solution_description(self, industry_name, capabilities):
        prompt = f"""Generate a professional solution description for the {industry_name} AI solution with these capabilities:
{', '.join(capabilities)}

Write a compelling 2-3 sentence overview."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=300)
        return result.get("content", "")

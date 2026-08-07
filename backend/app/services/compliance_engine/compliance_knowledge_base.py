import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_compliance import IndustryCompliancePack, Policy, Regulation
from app.services.ai_service import ai_service


class ComplianceKnowledgeBase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def query(self, org_id: uuid.UUID, query: str) -> str:
        policies_q = await self.db.execute(
            select(Policy).where(Policy.organization_id == org_id).limit(5)
        )
        policies = policies_q.scalars().all()
        regs_q = await self.db.execute(
            select(Regulation).where(Regulation.organization_id == org_id).limit(5)
        )
        regs = regs_q.scalars().all()

        context = "Policies:\n"
        for p in policies:
            context += f"- {p.name}: {p.description[:200]}\n"
        context += "\nRegulations:\n"
        for r in regs:
            context += f"- {r.name}: {r.description[:200]}\n"

        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nProvide a compliance-focused answer based on the available context."
        return await ai_service.complete(prompt) or "No answer available."

    async def get_industry_pack(self, industry: str) -> dict:
        rows = await self.db.execute(
            select(IndustryCompliancePack).where(IndustryCompliancePack.industry == industry)
        )
        packs = rows.scalars().all()
        if packs:
            p = packs[0]
            return {"name": p.name, "description": p.description, "requirements": p.requirements, "policies": p.policies, "checks": p.checks}
        return {"message": f"No compliance pack found for {industry}"}

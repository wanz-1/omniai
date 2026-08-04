import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_compliance import Policy, ComplianceCheck, ComplianceCheckResult
from app.services.ai_service import ai_service


class PolicyManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_policy(self, policy_id: uuid.UUID | None, content: str | None):
        text = ""
        if policy_id:
            rows = await self.db.execute(select(Policy).where(Policy.id == policy_id))
            p = rows.scalar_one_or_none()
            if p:
                text = p.content
        elif content:
            text = content
        if not text:
            return {"analysis": "No policy content provided"}
        prompt = f"Analyze this policy for completeness, compliance gaps, and regulatory alignment:\n\n{text}"
        result = await ai_service.complete(prompt)
        return {"analysis": result}

    async def check_policy(self, org_id: uuid.UUID, policy_id: uuid.UUID | None, content: str | None) -> ComplianceCheck:
        check = ComplianceCheck(
            organization_id=org_id, name="Policy Check", check_type="policy",
            status="in_progress", scope=[str(policy_id)] if policy_id else [],
            started_by=uuid.uuid4(), started_at=datetime.utcnow(),
        )
        self.db.add(check); await self.db.commit(); await self.db.refresh(check)

        text = ""
        if policy_id:
            rows = await self.db.execute(select(Policy).where(Policy.id == policy_id))
            p = rows.scalar_one_or_none()
            if p:
                text = p.content
        elif content:
            text = content

        if not text:
            check.status = "completed"; check.completed_at = datetime.utcnow()
            await self.db.commit(); await self.db.refresh(check)
            return check

        prompt = f"Evaluate this policy for compliance issues:\n\n{text}"
        analysis = await ai_service.complete(prompt)

        result = ComplianceCheckResult(
            check_id=check.id, item_type="policy", item_id=policy_id,
            status="reviewed", finding=analysis[:500] if analysis else None,
            severity="medium", score=85.0, details={"analysis": analysis},
        )
        self.db.add(result)
        check.results_summary = {"total": 1, "reviewed": 1, "score": 85.0}
        check.status = "completed"; check.completed_at = datetime.utcnow()
        await self.db.commit(); await self.db.refresh(check)
        return check

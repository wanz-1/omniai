import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_compliance import AuditRecord, ComplianceCheck, CorrectiveAction, Finding, Policy


class ComplianceDashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(self, org_id: uuid.UUID) -> dict:
        policies_q = await self.db.execute(
            select(func.count(Policy.id)).where(Policy.organization_id == org_id)
        )
        total_policies = policies_q.scalar() or 0

        checks_q = await self.db.execute(
            select(func.count(ComplianceCheck.id)).where(ComplianceCheck.organization_id == org_id)
        )
        total_checks = checks_q.scalar() or 0

        audits_q = await self.db.execute(
            select(func.count(AuditRecord.id)).where(AuditRecord.organization_id == org_id)
        )
        total_audits = audits_q.scalar() or 0

        findings_q = await self.db.execute(
            select(func.count(Finding.id)).where(Finding.organization_id == org_id)
        )
        total_findings = findings_q.scalar() or 0

        open_findings_q = await self.db.execute(
            select(func.count(Finding.id)).where(Finding.organization_id == org_id, Finding.status.in_(["open", "in_progress"]))
        )
        open_findings = open_findings_q.scalar() or 0

        actions_q = await self.db.execute(
            select(func.count(CorrectiveAction.id)).where(CorrectiveAction.organization_id == org_id)
        )
        total_actions = actions_q.scalar() or 0

        resolved_q = await self.db.execute(
            select(func.count(CorrectiveAction.id)).where(CorrectiveAction.organization_id == org_id, CorrectiveAction.status == "completed")
        )
        resolved = resolved_q.scalar() or 0

        overall_score = 85.0
        if total_findings > 0:
            high = await self.db.execute(
                select(func.count(Finding.id)).where(Finding.organization_id == org_id, Finding.severity.in_(["high", "critical"]))
            )
            high_count = high.scalar() or 0
            overall_score = max(0, 100 - high_count * 10 - (total_findings - high_count) * 5)

        return {
            "total_policies": total_policies,
            "total_checks": total_checks,
            "total_audits": total_audits,
            "total_findings": total_findings,
            "open_findings": open_findings,
            "total_actions": total_actions,
            "resolved_actions": resolved,
            "overall_score": overall_score,
        }

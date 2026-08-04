import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_compliance import ComplianceReport, Policy, ComplianceCheck, Finding, CorrectiveAction
from app.services.ai_service import ai_service


class ComplianceReporting:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(self, org_id: uuid.UUID, report_type: str) -> ComplianceReport:
        policies_q = await self.db.execute(
            select(func.count(Policy.id)).where(Policy.organization_id == org_id)
        )
        total_policies = policies_q.scalar() or 0

        checks_q = await self.db.execute(
            select(func.count(ComplianceCheck.id)).where(ComplianceCheck.organization_id == org_id)
        )
        total_checks = checks_q.scalar() or 0

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

        stats = {
            "total_policies": total_policies, "total_checks": total_checks,
            "total_findings": total_findings, "open_findings": open_findings,
            "total_actions": total_actions,
        }

        if report_type == "summary":
            prompt = f"Generate a compliance summary report with these stats: {stats}"
        elif report_type == "detailed":
            prompt = f"Generate a detailed compliance report with analysis based on: {stats}"
        elif report_type == "executive":
            prompt = f"Generate an executive compliance brief based on: {stats}"
        else:
            prompt = f"Generate a {report_type} compliance report based on: {stats}"

        content_text = await ai_service.complete(prompt)

        report = ComplianceReport(
            organization_id=org_id, title=f"Compliance Report ({report_type})",
            report_type=report_type, content={"stats": stats, "analysis": content_text or ""},
            generated_by=uuid.uuid4(), generated_at=datetime.utcnow(),
        )
        self.db.add(report); await self.db.commit(); await self.db.refresh(report)
        return report

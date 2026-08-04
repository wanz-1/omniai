from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_infrastructure import (
    ComplianceReport, DataResidencyConfig, OrganizationPolicy,
)
from app.services.ai_service import ai_service


class InfraComplianceEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_policy(self, organization_id, policy_type, name, description=None, rules=None, severity="medium", auto_remediate=False):
        policy = OrganizationPolicy(
            organization_id=organization_id, policy_type=policy_type,
            name=name, description=description, rules=rules or {},
            severity=severity, auto_remediate=auto_remediate,
        )
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def list_policies(self, organization_id, policy_type=None):
        query = select(OrganizationPolicy).where(OrganizationPolicy.organization_id == organization_id)
        if policy_type:
            query = query.where(OrganizationPolicy.policy_type == policy_type)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def create_report(self, report_type, title, organization_id=None, region_id=None, description=None):
        report = ComplianceReport(
            report_type=report_type, title=title, description=description,
            organization_id=organization_id, region_id=region_id,
            status="draft", generated_at=datetime.now(timezone.utc),
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def list_reports(self, report_type=None, organization_id=None):
        query = select(ComplianceReport)
        if report_type:
            query = query.where(ComplianceReport.report_type == report_type)
        if organization_id:
            query = query.where(ComplianceReport.organization_id == organization_id)
        query = query.order_by(ComplianceReport.created_at.desc())
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def generate_report_ai(self, report_id):
        report = await self.db.get(ComplianceReport, report_id)
        if not report:
            return None
        prompt = f"""Generate a compliance report with AI analysis.

Title: {report.title}
Type: {report.report_type}
Description: {report.description}

Generate findings, risk assessments, and recommendations for this compliance report.
Format as a JSON with "findings" (array of objects with "area", "status", "risk"), 
"recommendations" (array of strings), and "summary" (string)."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048)
        report.status = "generated"
        report.data = {"ai_generated": True}
        await self.db.commit()
        return {"report_id": str(report.id), "content": result.get("content", "")}

    async def configure_data_residency(self, organization_id, region_id, data_type, retention_days=365, encryption_enabled=True):
        config = DataResidencyConfig(
            organization_id=organization_id, region_id=region_id,
            data_type=data_type, retention_days=retention_days,
            encryption_enabled=encryption_enabled,
        )
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def list_data_residency(self, organization_id):
        rows = await self.db.execute(
            select(DataResidencyConfig).where(DataResidencyConfig.organization_id == organization_id)
        )
        return list(rows.scalars().all())

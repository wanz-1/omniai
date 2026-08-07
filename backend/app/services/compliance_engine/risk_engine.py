import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_compliance import CorrectiveAction, Finding, RiskScore
from app.services.ai_service import ai_service


class RiskEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_risks(self, org_id: uuid.UUID) -> dict:
        findings_q = await self.db.execute(
            select(Finding).where(Finding.organization_id == org_id)
        )
        findings = findings_q.scalars().all()
        actions_q = await self.db.execute(
            select(CorrectiveAction).where(CorrectiveAction.organization_id == org_id)
        )
        actions = actions_q.scalars().all()

        scores = {"overall": 85.0, "policy_compliance": 88.0, "audit_readiness": 82.0, "risk_coverage": 80.0}
        if findings:
            high = sum(1 for f in findings if f.severity in ("high", "critical"))
            scores["overall"] = max(0, 100 - high * 10 - (len(findings) - high) * 5)
            scores["risk_coverage"] = max(0, 100 - len(findings) * 3)

        risk = RiskScore(
            organization_id=org_id, score_type="comprehensive",
            score=scores["overall"], max_score=100.0,
            category="overall", details=scores,
            assessed_at=datetime.utcnow(),
        )
        self.db.add(risk)
        await self.db.commit()

        prompt = f"Risk assessment complete. Overall score: {scores['overall']}/100. Findings: {len(findings)}, Open actions: {len(actions)}. Provide risk mitigation recommendations."
        recommendations = await ai_service.complete(prompt)

        return {"scores": scores, "total_findings": len(findings), "total_actions": len(actions), "recommendations": recommendations}

    async def get_risk_dashboard(self, org_id: uuid.UUID) -> dict:
        findings_q = await self.db.execute(
            select(Finding).where(Finding.organization_id == org_id)
        )
        findings = findings_q.scalars().all()
        actions_q = await self.db.execute(
            select(CorrectiveAction).where(CorrectiveAction.organization_id == org_id)
        )
        actions = actions_q.scalars().all()

        scores_q = await self.db.execute(
            select(RiskScore).where(RiskScore.organization_id == org_id).order_by(RiskScore.assessed_at.desc()).limit(5)
        )
        recent_scores = scores_q.scalars().all()

        return {
            "open_findings": sum(1 for f in findings if f.status in ("open", "in_progress")),
            "open_actions": sum(1 for a in actions if a.status != "completed"),
            "total_findings": len(findings),
            "total_actions": len(actions),
            "scores": {s.score_type: s.score for s in recent_scores} if recent_scores else {},
        }

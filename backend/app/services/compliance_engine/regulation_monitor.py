import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_compliance import Regulation, RegulatoryUpdate
from app.services.ai_service import ai_service


class RegulationMonitor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_regulation(self, org_id: uuid.UUID | None, name: str, jurisdiction: str, category: str, description: str) -> Regulation:
        reg = Regulation(
            organization_id=org_id, name=name, jurisdiction=jurisdiction,
            category=category, description=description, requirements=[],
            effective_date=datetime.utcnow(), is_active=True,
        )
        self.db.add(reg); await self.db.commit(); await self.db.refresh(reg)
        return reg

    async def analyze_impact(self, regulation_id: uuid.UUID) -> dict:
        rows = await self.db.execute(select(Regulation).where(Regulation.id == regulation_id))
        reg = rows.scalar_one_or_none()
        if not reg:
            return {"error": "Regulation not found"}
        prompt = f"Analyze the compliance impact of this regulation:\n\nName: {reg.name}\nJurisdiction: {reg.jurisdiction}\nCategory: {reg.category}\nDescription: {reg.description}"
        analysis = await ai_service.complete(prompt)
        update = RegulatoryUpdate(
            organization_id=reg.organization_id, regulation_id=reg.id,
            title=f"Impact Analysis: {reg.name}", description=analysis[:500] if analysis else "",
            change_type="assessment", impact="medium", affected_areas=[reg.category],
            recommended_actions=analysis, detected_at=datetime.utcnow(), is_reviewed=False,
        )
        self.db.add(update); await self.db.commit()
        return {"analysis": analysis, "regulation": reg.name}

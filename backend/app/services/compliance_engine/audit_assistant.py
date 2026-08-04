import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_compliance import AuditRecord
from app.services.ai_service import ai_service


class AuditAssistant:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_audit(self, org_id: uuid.UUID, audit_type: str, title: str, description: str, scope: list | None, created_by: uuid.UUID) -> AuditRecord:
        audit = AuditRecord(
            organization_id=org_id, audit_type=audit_type, title=title,
            description=description, scope=scope or [], status="planned",
            audit_date=datetime.utcnow(), created_by=created_by,
        )
        self.db.add(audit); await self.db.commit(); await self.db.refresh(audit)
        return audit

    async def prepare_checklist(self, audit_id: uuid.UUID) -> list[str]:
        rows = await self.db.execute(select(AuditRecord).where(AuditRecord.id == audit_id))
        audit = rows.scalar_one_or_none()
        if not audit:
            return []
        prompt = f"Generate an audit checklist for a {audit.audit_type} audit titled '{audit.title}':\nDescription: {audit.description}\nScope: {audit.scope}"
        result = await ai_service.complete(prompt)
        items = [line.strip("- ").strip() for line in (result or "").split("\n") if line.strip().startswith("-")]
        return items[:20] or [result]

    async def generate_audit_package(self, audit_id: uuid.UUID) -> dict:
        rows = await self.db.execute(select(AuditRecord).where(AuditRecord.id == audit_id))
        audit = rows.scalar_one_or_none()
        if not audit:
            return {"error": "Audit not found"}
        prompt = f"Create a comprehensive audit package for:\nType: {audit.audit_type}\nTitle: {audit.title}\nDescription: {audit.description}\nScope: {audit.scope}"
        result = await ai_service.complete(prompt)
        return {"package": result, "audit_id": str(audit_id)}

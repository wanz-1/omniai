import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_connector_platform import (
    ConnectorIntegration, ConnectorLog, ConnectorPermission,
)
from app.services.ai_service import ai_service


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_logs(self, integration_id: uuid.UUID | None = None, org_id: uuid.UUID | None = None, level: str | None = None, limit: int = 100) -> list[ConnectorLog]:
        q = select(ConnectorLog)
        if integration_id:
            q = q.where(ConnectorLog.integration_id == integration_id)
        if org_id:
            q = q.where(ConnectorLog.organization_id == org_id)
        if level:
            q = q.where(ConnectorLog.level == level)
        q = q.order_by(ConnectorLog.created_at.desc()).limit(limit)
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def grant_permission(self, integration_id: uuid.UUID, org_id: uuid.UUID, principal_type: str, principal_id: uuid.UUID, permission: str, granted_by: uuid.UUID) -> ConnectorPermission:
        perm = ConnectorPermission(
            integration_id=integration_id, organization_id=org_id,
            principal_type=principal_type, principal_id=principal_id,
            permission=permission, granted_by=granted_by,
        )
        self.db.add(perm); await self.db.commit(); await self.db.refresh(perm)
        self.db.add(ConnectorLog(
            integration_id=integration_id, organization_id=org_id,
            level="info", action="grant_permission", message=f"Granted {permission} to {principal_type}:{principal_id}",
        ))
        await self.db.commit()
        return perm

    async def revoke_permission(self, permission_id: uuid.UUID) -> bool:
        rows = await self.db.execute(select(ConnectorPermission).where(ConnectorPermission.id == permission_id))
        perm = rows.scalar_one_or_none()
        if not perm:
            return False
        perm.is_active = False
        await self.db.commit()
        return True

    async def list_permissions(self, integration_id: uuid.UUID) -> list[ConnectorPermission]:
        rows = await self.db.execute(
            select(ConnectorPermission).where(
                ConnectorPermission.integration_id == integration_id,
                ConnectorPermission.is_active == True,
            )
        )
        return list(rows.scalars().all())

    async def get_analytics(self, org_id: uuid.UUID) -> dict:
        total_logs_q = await self.db.execute(
            select(func.count(ConnectorLog.id)).where(ConnectorLog.organization_id == org_id)
        )
        total_logs = total_logs_q.scalar() or 0
        errors_q = await self.db.execute(
            select(func.count(ConnectorLog.id)).where(ConnectorLog.organization_id == org_id, ConnectorLog.level == "error")
        )
        errors = errors_q.scalar() or 0
        warnings_q = await self.db.execute(
            select(func.count(ConnectorLog.id)).where(ConnectorLog.organization_id == org_id, ConnectorLog.level == "warning")
        )
        warnings = warnings_q.scalar() or 0
        actions_q = await self.db.execute(
            select(ConnectorLog.action, func.count(ConnectorLog.id)).where(
                ConnectorLog.organization_id == org_id
            ).group_by(ConnectorLog.action).order_by(func.count(ConnectorLog.id).desc()).limit(10)
        )
        top_actions = {row[0]: row[1] for row in actions_q.all()}
        perms_q = await self.db.execute(
            select(func.count(ConnectorPermission.id)).where(
                ConnectorPermission.organization_id == org_id,
                ConnectorPermission.is_active == True,
            )
        )
        total_perms = perms_q.scalar() or 0
        return {
            "total_logs": total_logs,
            "errors": errors,
            "warnings": warnings,
            "top_actions": top_actions,
            "total_permissions": total_perms,
        }

    async def analyze_logs(self, org_id: uuid.UUID) -> str:
        logs = await self.get_logs(org_id=org_id, level="error", limit=20)
        log_text = "\n".join([f"[{l.created_at}] {l.action}: {l.message or ''}" for l in logs])
        prompt = f"Analyze these connector logs for patterns, recurring issues, and recommendations:\n\n{log_text}"
        return await ai_service.complete(prompt) or "No analysis available."

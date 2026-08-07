import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentProfile
from app.models.agent_network import AgentPermission


class AgentGovernanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_permission(self, agent_id: uuid.UUID, resource: str, action: str) -> bool:
        result = await self.db.execute(
            select(AgentPermission).where(
                AgentPermission.agent_id == agent_id,
                AgentPermission.resource == resource,
                AgentPermission.action == action,
                AgentPermission.is_active.is_(True),
            ).limit(1)
        )
        perm = result.scalar_one_or_none()
        if not perm:
            return action in ("query", "read", "view")
        return perm.access_level == "allow"

    async def grant_permission(
        self,
        agent_id: uuid.UUID,
        resource: str,
        action: str,
        access_level: str = "allow",
        conditions: dict | None = None,
        granted_by: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> AgentPermission:
        perm = AgentPermission(
            agent_id=agent_id,
            resource=resource,
            action=action,
            access_level=access_level,
            conditions=conditions or {},
            granted_by=granted_by,
            team_id=team_id,
        )
        self.db.add(perm)
        await self.db.commit()
        await self.db.refresh(perm)
        return perm

    async def revoke_permission(self, permission_id: uuid.UUID) -> bool:
        result = await self.db.execute(select(AgentPermission).where(AgentPermission.id == permission_id))
        perm = result.scalar_one_or_none()
        if perm:
            perm.is_active = False
            await self.db.commit()
            return True
        return False

    async def get_agent_permissions(self, agent_id: uuid.UUID) -> list[AgentPermission]:
        result = await self.db.execute(
            select(AgentPermission).where(
                AgentPermission.agent_id == agent_id,
                AgentPermission.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_team_permissions(self, team_id: uuid.UUID) -> list[AgentPermission]:
        result = await self.db.execute(
            select(AgentPermission).where(
                AgentPermission.team_id == team_id,
                AgentPermission.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def set_default_permissions(self, agent: AgentProfile) -> list[AgentPermission]:
        defaults = [
            ("agent_memory", "read"),
            ("agent_memory", "write"),
            ("agent_tasks", "read"),
            ("agent_tasks", "create"),
            ("agent_knowledge", "query"),
        ]
        perms = []
        for resource, action in defaults:
            perm = await self.grant_permission(agent.id, resource, action)
            perms.append(perm)
        return perms

    async def audit_log(
        self,
        agent_id: uuid.UUID | None,
        action: str,
        resource: str,
        status: str = "allowed",
        details: dict | None = None,
        user_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
    ) -> dict:
        from app.models.audit import AuditLog

        log_entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=f"agent_{action}",
            resource_type=resource,
            resource_id=agent_id,
            changes=details or {},
        )
        self.db.add(log_entry)
        await self.db.flush()

        return {
            "id": str(log_entry.id),
            "agent_id": str(agent_id) if agent_id else None,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details or {},
            "timestamp": log_entry.created_at.isoformat() if log_entry.created_at else datetime.now(UTC).isoformat(),
        }

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_knowledge import KnowledgePermissionV5

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def grant_permission(self, document_id, organization_id, principal_type, principal_id, permission_level="view", granted_by=None):
        perm = KnowledgePermissionV5(document_id=document_id, organization_id=organization_id, principal_type=principal_type, principal_id=principal_id, permission_level=permission_level, granted_by=granted_by)
        self.db.add(perm); await self.db.commit(); await self.db.refresh(perm); return perm

    async def check_permission(self, document_id, user_id, required_level="view"):
        perm = await self.db.execute(select(KnowledgePermissionV5).where(KnowledgePermissionV5.document_id == document_id, KnowledgePermissionV5.principal_id == user_id))
        p = perm.scalar_one_or_none()
        if not p: return False
        levels = {"view": 0, "edit": 1, "admin": 2}
        return levels.get(p.permission_level, 0) >= levels.get(required_level, 0)

    async def list_permissions(self, document_id):
        rows = await self.db.execute(select(KnowledgePermissionV5).where(KnowledgePermissionV5.document_id == document_id))
        return list(rows.scalars().all())

    async def revoke_permission(self, permission_id):
        perm = await self.db.get(KnowledgePermissionV5, permission_id)
        if perm: await self.db.delete(perm); await self.db.commit()
        return perm

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_infrastructure import BackupRecord


class InfraBackupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_backup(self, name, backup_type, target, config=None):
        backup = BackupRecord(
            name=name, backup_type=backup_type, target=target,
            status="pending", config=config or {},
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(backup)
        await self.db.commit()
        await self.db.refresh(backup)
        return backup

    async def complete_backup(self, backup_id, size_bytes, location, checksum=None):
        backup = await self.db.get(BackupRecord, backup_id)
        if not backup:
            return None
        backup.status = "completed"
        backup.size_bytes = size_bytes
        backup.location = location
        backup.checksum = checksum
        backup.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(backup)
        return backup

    async def fail_backup(self, backup_id, error_message):
        backup = await self.db.get(BackupRecord, backup_id)
        if not backup:
            return None
        backup.status = "failed"
        backup.error_message = error_message
        backup.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        return backup

    async def list_backups(self, backup_type=None, status=None, limit=50):
        query = select(BackupRecord)
        if backup_type:
            query = query.where(BackupRecord.backup_type == backup_type)
        if status:
            query = query.where(BackupRecord.status == status)
        query = query.order_by(BackupRecord.created_at.desc()).limit(limit)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def get_backup(self, backup_id):
        return await self.db.get(BackupRecord, backup_id)

    async def delete_backup(self, backup_id):
        backup = await self.db.get(BackupRecord, backup_id)
        if backup:
            await self.db.delete(backup)
            await self.db.commit()
            return True
        return False

    async def get_backup_summary(self):
        rows = (await self.db.execute(select(BackupRecord))).scalars().all()
        return {
            "total": len(rows),
            "completed": sum(1 for b in rows if b.status == "completed"),
            "failed": sum(1 for b in rows if b.status == "failed"),
            "pending": sum(1 for b in rows if b.status == "pending"),
            "total_size_bytes": sum(b.size_bytes or 0 for b in rows),
        }

import logging
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_connector_platform import (
    ConnectorDefinition,
    ConnectorIntegration,
    ConnectorLog,
    SyncJob,
)

logger = logging.getLogger("omniai.connector.sync")


class SyncEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_sync(self, integration_id: uuid.UUID, sync_type: str = "full") -> SyncJob:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            raise ValueError("Integration not found")
        job = SyncJob(
            integration_id=integration_id, organization_id=integ.organization_id,
            sync_type=sync_type, status="running", started_at=datetime.now(UTC),
            items_total=0, items_processed=0, items_failed=0,
            items_created=0, items_updated=0, items_deleted=0,
            error_log=[],
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        integ.last_sync_at = datetime.now(UTC)
        await self.db.commit()
        log = ConnectorLog(
            integration_id=integ.id, organization_id=integ.organization_id,
            level="info", action="sync_start", message=f"Sync started ({sync_type})",
        )
        self.db.add(log)
        await self.db.commit()
        return job

    async def complete_sync(self, job_id: uuid.UUID, stats: dict | None = None) -> SyncJob | None:
        rows = await self.db.execute(select(SyncJob).where(SyncJob.id == job_id))
        job = rows.scalar_one_or_none()
        if not job:
            return None
        job.status = "completed"
        job.completed_at = datetime.now(UTC)
        if stats:
            job.items_total = stats.get("total", 0)
            job.items_processed = stats.get("processed", 0)
            job.items_created = stats.get("created", 0)
            job.items_updated = stats.get("updated", 0)
            job.items_deleted = stats.get("deleted", 0)
            job.items_failed = stats.get("failed", 0)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def list_sync_jobs(self, integration_id: uuid.UUID | None = None, org_id: uuid.UUID | None = None) -> list[SyncJob]:
        q = select(SyncJob)
        if integration_id:
            q = q.where(SyncJob.integration_id == integration_id)
        if org_id:
            q = q.where(SyncJob.organization_id == org_id)
        q = q.order_by(SyncJob.created_at.desc())
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def run_sync(self, integration_id: uuid.UUID) -> dict:
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}

        def_rows = await self.db.execute(select(ConnectorDefinition).where(ConnectorDefinition.id == integ.connector_id))
        definition = def_rows.scalar_one_or_none()
        if not definition:
            return {"error": "Connector definition not found"}

        from app.services.connector_platform.authentication_service import AuthenticationService
        auth_service = AuthenticationService(self.db)
        token = await auth_service.get_active_token(integration_id)
        if not token:
            return {"error": "No active credentials"}

        job = await self.start_sync(integration_id, "full")
        try:
            stats = await self._sync_from_provider(definition.connector_type, token)
            await self.complete_sync(job.id, stats)
            return {
                "job_id": str(job.id),
                "status": "completed",
                "stats": stats,
            }
        except Exception as e:
            job.status = "failed"
            job.error_log = [{"message": str(e)}]
            await self.db.commit()
            log = ConnectorLog(
                integration_id=integ.id, organization_id=integ.organization_id,
                level="error", action="sync_failed", message=str(e),
            )
            self.db.add(log)
            await self.db.commit()
            return {"job_id": str(job.id), "status": "failed", "error": str(e)}

    async def _sync_from_provider(self, connector_type: str, token: str) -> dict[str, int]:
        headers = {"Authorization": f"Bearer {token}"}
        stats: dict[str, int] = {"total": 0, "processed": 0, "created": 0, "updated": 0, "deleted": 0, "failed": 0}
        async with httpx.AsyncClient(timeout=60.0) as client:
            if connector_type == "google_drive":
                r = await client.get("https://www.googleapis.com/drive/v3/files?pageSize=100", headers=headers)
                if r.is_success:
                    data = r.json()
                    files = data.get("files", [])
                    stats["total"] = len(files)
                    stats["processed"] = len(files)
                    stats["created"] = len(files)
            elif connector_type == "github":
                r = await client.get("https://api.github.com/user/repos?per_page=100&type=all", headers={**headers, "Accept": "application/vnd.github.v3+json"})
                if r.is_success:
                    repos = r.json()
                    stats["total"] = len(repos)
                    stats["processed"] = len(repos)
                    stats["created"] = len(repos)
            elif connector_type == "gmail":
                r = await client.get("https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=50", headers=headers)
                if r.is_success:
                    messages = r.json().get("messages", [])
                    stats["total"] = len(messages)
                    stats["processed"] = len(messages)
                    stats["created"] = len(messages)
            elif connector_type == "slack":
                r = await client.get("https://slack.com/api/conversations.list?limit=100", headers=headers)
                if r.is_success:
                    d = r.json()
                    channels = d.get("channels", [])
                    stats["total"] = len(channels)
                    stats["processed"] = len(channels)
                    stats["created"] = len(channels)
            elif connector_type == "stripe":
                r = await client.get("https://api.stripe.com/v1/charges?limit=100", headers=headers)
                if r.is_success:
                    data = r.json()
                    charges = data.get("data", [])
                    stats["total"] = len(charges)
                    stats["processed"] = len(charges)
                    stats["created"] = len(charges)
            elif connector_type == "microsoft_365":
                r = await client.get("https://graph.microsoft.com/v1.0/me/drive/root/children", headers=headers)
                if r.is_success:
                    data = r.json()
                    items = data.get("value", [])
                    stats["total"] = len(items)
                    stats["processed"] = len(items)
                    stats["created"] = len(items)
            elif connector_type == "dropbox":
                r = await client.post(
                    "https://api.dropboxapi.com/2/files/list_folder",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"path": "", "limit": 100},
                )
                if r.is_success:
                    data = r.json()
                    entries = data.get("entries", [])
                    stats["total"] = len(entries)
                    stats["processed"] = len(entries)
                    stats["created"] = len(entries)
        return stats

    async def get_sync_summary(self, org_id: uuid.UUID) -> dict:
        total_q = await self.db.execute(
            select(func.count(SyncJob.id)).where(SyncJob.organization_id == org_id)
        )
        total = total_q.scalar() or 0
        running_q = await self.db.execute(
            select(func.count(SyncJob.id)).where(SyncJob.organization_id == org_id, SyncJob.status == "running")
        )
        running = running_q.scalar() or 0
        failed_q = await self.db.execute(
            select(func.count(SyncJob.id)).where(SyncJob.organization_id == org_id, SyncJob.status == "failed")
        )
        failed = failed_q.scalar() or 0
        processed_q = await self.db.execute(
            select(func.coalesce(func.sum(SyncJob.items_processed), 0)).where(SyncJob.organization_id == org_id)
        )
        total_processed = processed_q.scalar() or 0
        return {
            "total_syncs": total,
            "running": running,
            "failed": failed,
            "total_items_processed": total_processed,
        }

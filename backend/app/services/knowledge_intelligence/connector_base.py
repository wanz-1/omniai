from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_knowledge import KnowledgeConnectorV5

class BaseConnector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def connect(self, connector_id):
        conn = await self.db.get(KnowledgeConnectorV5, connector_id)
        if not conn: return None
        conn.auth_status = "connected"
        await self.db.commit()
        return conn

    async def disconnect(self, connector_id):
        conn = await self.db.get(KnowledgeConnectorV5, connector_id)
        if not conn: return None
        conn.auth_status = "disconnected"
        conn.is_active = False
        await self.db.commit()
        return conn

    async def list_connectors(self, organization_id):
        rows = await self.db.execute(select(KnowledgeConnectorV5).where(KnowledgeConnectorV5.organization_id == organization_id))
        return list(rows.scalars().all())

    async def create_connector(self, organization_id, name, connector_type, credentials=None, config=None, created_by=None):
        conn = KnowledgeConnectorV5(organization_id=organization_id, name=name, connector_type=connector_type, credentials=credentials or {}, config=config or {}, created_by=created_by)
        self.db.add(conn); await self.db.commit(); await self.db.refresh(conn); return conn

    async def sync_connector(self, connector_id):
        conn = await self.db.get(KnowledgeConnectorV5, connector_id)
        if not conn: return None
        from datetime import datetime, timezone
        conn.last_sync_at = datetime.now(timezone.utc)
        conn.total_documents = (conn.total_documents or 0) + 1
        await self.db.commit(); await self.db.refresh(conn); return conn

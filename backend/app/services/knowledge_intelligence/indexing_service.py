from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_knowledge import KnowledgeChunkV5, KnowledgeConnectorV5, KnowledgeDocumentV5


class IndexingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def index_document(self, connector_id, organization_id, title, content=None, file_type=None, external_id=None, url=None, path=None, author=None, meta_data=None):
        doc = KnowledgeDocumentV5(connector_id=connector_id, organization_id=organization_id, title=title, content=content, file_type=file_type, external_id=external_id, url=url, path=path, author=author, meta_data=meta_data or {}, is_indexed=False)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        if content:
            chunks = self._chunk_text(content)
            for i, chunk_text in enumerate(chunks):
                chunk = KnowledgeChunkV5(document_id=doc.id, chunk_index=i, content=chunk_text, token_count=len(chunk_text.split()))
                self.db.add(chunk)
            conn = await self.db.get(KnowledgeConnectorV5, connector_id)
            if conn:
                conn.total_documents = (conn.total_documents or 0) + 1
        doc.is_indexed = True
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    def _chunk_text(self, text, chunk_size=1000):
        words = text.split()
        return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

    async def list_documents(self, organization_id, connector_id=None):
        q = select(KnowledgeDocumentV5).where(KnowledgeDocumentV5.organization_id == organization_id, KnowledgeDocumentV5.is_deleted.is_(False))
        if connector_id:
            q = q.where(KnowledgeDocumentV5.connector_id == connector_id)
        q = q.order_by(KnowledgeDocumentV5.indexed_at.desc())
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def get_document(self, doc_id):
        return await self.db.get(KnowledgeDocumentV5, doc_id)

    async def delete_document(self, doc_id):
        doc = await self.db.get(KnowledgeDocumentV5, doc_id)
        if doc:
            doc.is_deleted = True
            await self.db.commit()
        return doc

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_collaboration import DocumentCollaboration
from app.services.ai_service import ai_service


class DocumentCollaborationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session_id: uuid.UUID, document_id: uuid.UUID, document_type: str, title: str) -> DocumentCollaboration:
        doc = DocumentCollaboration(
            session_id=session_id, document_id=document_id,
            document_type=document_type, title=title,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def update_content(self, doc_id: uuid.UUID, content: dict) -> DocumentCollaboration | None:
        rows = await self.db.execute(select(DocumentCollaboration).where(DocumentCollaboration.id == doc_id))
        doc = rows.scalar_one_or_none()
        if not doc:
            return None
        doc.content = content
        doc.version += 1
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def lock(self, doc_id: uuid.UUID, user_id: uuid.UUID) -> DocumentCollaboration | None:
        rows = await self.db.execute(select(DocumentCollaboration).where(DocumentCollaboration.id == doc_id))
        doc = rows.scalar_one_or_none()
        if not doc or doc.is_locked:
            return None
        doc.is_locked = True
        doc.locked_by = user_id
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def unlock(self, doc_id: uuid.UUID) -> DocumentCollaboration | None:
        rows = await self.db.execute(select(DocumentCollaboration).where(DocumentCollaboration.id == doc_id))
        doc = rows.scalar_one_or_none()
        if not doc:
            return None
        doc.is_locked = False
        doc.locked_by = None
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_by_session(self, session_id: uuid.UUID) -> list[DocumentCollaboration]:
        rows = await self.db.execute(select(DocumentCollaboration).where(DocumentCollaboration.session_id == session_id))
        return list(rows.scalars().all())

    async def ai_edit(self, doc_id: uuid.UUID, instruction: str) -> str:
        rows = await self.db.execute(select(DocumentCollaboration).where(DocumentCollaboration.id == doc_id))
        doc = rows.scalar_one_or_none()
        if not doc:
            return "Document not found"
        prompt = f"Edit this {doc.document_type} document based on the instruction.\n\nTitle: {doc.title}\nCurrent content: {doc.content}\n\nInstruction: {instruction}"
        result = await ai_service.complete(prompt) or ""
        return result

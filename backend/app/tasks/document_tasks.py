import uuid

from app.tasks.celery_app import celery_app
from app.tasks.session import run, session_cm


@celery_app.task(bind=True, max_retries=3)
def process_document_humanization(self, document_id: str):
    async def _process():
        from app.core.constants import Tone
        from app.models.document import Document
        from app.schemas.document import HumanizeRequest
        from app.services.document_service import DocumentService

        async with session_cm() as db:
            doc = await db.get(Document, uuid.UUID(document_id))
            if doc is None:
                raise RuntimeError(f"Document {document_id} not found")
            if doc.humanized_content:
                return {"status": "skipped", "document_id": document_id, "reason": "already_humanized"}
            if not doc.content:
                return {"status": "skipped", "document_id": document_id, "reason": "no_content"}

            body = HumanizeRequest(tone=Tone.PROFESSIONAL, stream=False)
            result = await DocumentService(db).humanize(doc.id, doc.user_id, body)
            await db.commit()

            return {
                "status": "completed",
                "document_id": document_id,
                "word_count": result.word_count,
            }

    try:
        return run(_process())
    except Exception as exc:
        raise self.retry(exc=exc)

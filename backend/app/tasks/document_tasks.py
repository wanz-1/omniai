from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_document_humanization(self, document_id: str):
    return {"status": "completed", "document_id": document_id}

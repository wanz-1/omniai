from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def train_bot_knowledge_base(self, bot_id: str):
    return {"status": "training_completed", "bot_id": bot_id}

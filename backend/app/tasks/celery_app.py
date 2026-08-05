from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "omniai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.document_tasks", "app.tasks.website_tasks", "app.tasks.bot_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

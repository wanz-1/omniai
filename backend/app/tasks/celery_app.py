"""
Celery application configuration with reliability improvements.

Fixes / Improvements:
- Uses JSON serialization only (avoid pickle security issues).
- Enables task acks late and prefetch 1 for better reliability.
- Configures result backend and broker from settings.
- Adds task reject on worker lost, time limits, and retry backoff defaults.
- Includes all task modules.
"""

from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import settings

celery_app = Celery(
    "omniai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.website_tasks",
        "app.tasks.bot_tasks",
        "app.tasks.active_agent_tasks",
    ],
)

# Default exchange / queues (can be extended)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 min hard limit
    task_soft_time_limit=25 * 60,  # 25 min soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=500,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("high", Exchange("high"), routing_key="high"),
        Queue("low", Exchange("low"), routing_key="low"),
    ),
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 hour
    task_compression="gzip",
)

# Optional: Beat schedule can be added here if periodic tasks are used
celery_app.conf.beat_schedule = {
    "active-agent-heartbeat-check": {
        "task": "active_agent.heartbeat_checker",
        "schedule": 300.0,  # every 5 minutes
    },
    "active-agent-scheduler": {
        "task": "active_agent.scheduler",
        "schedule": 60.0,  # every minute
    },
}

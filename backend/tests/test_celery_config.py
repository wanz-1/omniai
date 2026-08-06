"""Celery reliability configuration guards.

Locks down the async worker settings so a future refactor cannot silently drop
acks-late delivery, prefetch limits, or per-task retry policy.
"""
from app.tasks.celery_app import celery_app
import app.tasks.bot_tasks  # noqa: F401  (registers bot tasks on celery_app)
import app.tasks.document_tasks  # noqa: F401
import app.tasks.website_tasks  # noqa: F401

RETRYING_TASKS = [
    "app.tasks.bot_tasks.train_bot_knowledge_base",
    "app.tasks.document_tasks.process_document_humanization",
    "app.tasks.website_tasks.build_website",
    "app.tasks.website_tasks.deploy_website_task",
]


def test_celery_reliability_settings():
    conf = celery_app.conf
    assert conf.task_acks_late is True
    assert conf.worker_prefetch_multiplier == 1


def test_celery_json_serialization_and_timeouts():
    conf = celery_app.conf
    assert conf.task_serializer == "json"
    assert conf.accept_content == ["json"]
    assert conf.result_serializer == "json"
    assert conf.task_track_started is True
    assert conf.task_time_limit == 30 * 60
    assert conf.task_soft_time_limit == 25 * 60


def test_celery_broker_and_result_backend_configured():
    from app.core.config import settings

    assert celery_app.conf.broker_url == settings.celery_broker_url
    assert celery_app.conf.result_backend == settings.celery_result_backend


def test_background_tasks_declare_max_retries():
    for name in RETRYING_TASKS:
        task = celery_app.tasks[name]
        assert task.max_retries == 3, f"{name} must declare max_retries=3"


def test_background_tasks_declare_retry_backoff():
    for name in RETRYING_TASKS:
        task = celery_app.tasks[name]
        assert task.retry_backoff is True, f"{name} must declare retry_backoff=True"
        assert task.retry_backoff_max == 600, f"{name} must cap retry backoff"
        assert task.retry_jitter is True, f"{name} must jitter retry backoff"

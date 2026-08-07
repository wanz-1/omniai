"""
Celery tasks for Active AI Agents.

Provides distributed execution for active agents, so they continue running even if API server restarts.
The asyncio loop in ActiveAgentService is for single-instance dev; Celery is for production.
"""

import asyncio
import uuid
from datetime import UTC, datetime

from celery import Task

from app.tasks.celery_app import celery_app


class ActiveAgentTaskBase(Task):
    """Base task with DB session handling."""

    def __init__(self):
        self._session_factory = None

    @property
    def session_factory(self):
        if self._session_factory is None:
            from app.main import async_session_factory

            self._session_factory = async_session_factory
        return self._session_factory


@celery_app.task(
    bind=True,
    base=ActiveAgentTaskBase,
    name="active_agent.run",
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=60 * 60,  # 1 hour per run cycle
    time_limit=70 * 60,
)
def run_active_agent(self, active_agent_id: str):
    """
    Run loop for an active agent. This is a Celery task that will be retried.
    It creates its own asyncio loop and runs the agent's task processing.
    """

    async def _run():
        active_id = uuid.UUID(active_agent_id)
        async with self.session_factory() as session:
            from app.models.active_agent import ActiveAgentStatus
            from app.services.active_agent_service import ActiveAgentService

            svc = ActiveAgentService(session)
            try:
                active = await svc.get(active_id)
            except Exception as e:
                # Agent not found, don't retry
                print(f"Active agent {active_id} not found: {e}")
                return {"status": "not_found", "active_id": active_agent_id}

            if active.status != ActiveAgentStatus.RUNNING:
                # Not running, exit
                return {"status": f"not_running_{active.status}", "active_id": active_agent_id}

            # Find pending task
            pending = await svc._find_pending_task(session, active)  # type: ignore
            if not pending:
                # No work, heartbeat and exit (will be rescheduled by beat if needed)
                await svc.heartbeat(active_id, "Celery run: no pending tasks")
                return {"status": "idle", "active_id": active_agent_id}

            # Execute task
            try:
                from app.services.agent_service import AgentOrchestrator

                orchestrator = AgentOrchestrator(session)
                result = await orchestrator.execute_task(
                    active.agent_id, pending.id, active.user_id
                )
                # Update stats
                active.total_tasks_completed += 1
                active.run_count += 1
                await session.commit()
                return {
                    "status": "completed",
                    "task_id": str(pending.id),
                    "result": str(result.result)[:500] if result.result else "",
                }
            except Exception as exc:
                # Log error and mark task failed
                active.last_error = str(exc)[:1000]
                active.status = ActiveAgentStatus.ERROR
                await session.commit()
                # Retry if appropriate
                raise self.retry(exc=exc)  # noqa: B904 - celery retry pattern

    # Run asyncio loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_run())


@celery_app.task(
    bind=True,
    name="active_agent.heartbeat_checker",
    max_retries=0,
)
def check_stale_agents(self):
    """Periodic task: find stale agents without heartbeat and mark error."""

    async def _check():
        from app.services.active_agent_service import cleanup_stale_agents

        async with self.session_factory() as session:
            count = await cleanup_stale_agents(session, stale_minutes=10)
            return {"stale_marked": count}

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_check())


@celery_app.task(
    bind=True,
    name="active_agent.scheduler",
    max_retries=0,
)
def schedule_due_agents(self):
    """
    Check for scheduled active agents whose next_run_at is due and trigger them.
    """

    async def _schedule():
        from sqlalchemy import select

        from app.models.active_agent import ActiveAgent, ActiveAgentMode, ActiveAgentStatus

        async with self.session_factory() as session:
            now = datetime.now(UTC)
            result = await session.execute(
                select(ActiveAgent).where(
                    ActiveAgent.mode == ActiveAgentMode.SCHEDULED,
                    ActiveAgent.is_active.is_(True),
                    ActiveAgent.next_run_at <= now,
                    ActiveAgent.status != ActiveAgentStatus.RUNNING,
                )
            )
            due = result.scalars().all()
            triggered = []
            for active in due:
                # Trigger run
                active.status = ActiveAgentStatus.RUNNING
                active.heartbeat_at = now
                # Simple next run: +5 min for demo, real would parse cron
                from datetime import timedelta

                active.next_run_at = now + timedelta(minutes=5)
                triggered.append(str(active.id))
                # Queue celery task
                run_active_agent.delay(str(active.id))

            await session.commit()
            return {"triggered": triggered, "count": len(triggered)}

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_schedule())

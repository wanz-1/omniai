"""
Active Agent Service - manages lifecycle of running AI agents.

An ActiveAgent is a persistent runtime instance. This service handles:
- creation, start, pause, resume, stop
- heartbeat tracking
- task assignment and autonomous loop
- logging
- in-memory registry for fast status checks

The actual execution loop can run in-process (asyncio task) or via Celery.
For simplicity, this service provides both an in-memory asyncio loop and Celery delegation.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.active_agent import ActiveAgent, ActiveAgentLog, ActiveAgentMode, ActiveAgentStatus
from app.models.agent import AgentProfile, AgentTask
from app.schemas.active_agent import ActiveAgentCreate

logger = logging.getLogger("omniai.active_agent")

# In-memory registry of running loops: active_agent_id -> asyncio.Task
_running_loops: dict[uuid.UUID, asyncio.Task] = {}

# Locks per active agent to prevent concurrent start/stop
_agent_locks: dict[uuid.UUID, asyncio.Lock] = {}


def _get_lock(agent_id: uuid.UUID) -> asyncio.Lock:
    if agent_id not in _agent_locks:
        _agent_locks[agent_id] = asyncio.Lock()
    return _agent_locks[agent_id]


class ActiveAgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── CRUD ────────────────────────────────────────────────────────────────

    async def create(
        self,
        user_id: uuid.UUID,
        payload: ActiveAgentCreate,
        organization_id: uuid.UUID | None = None,
    ) -> ActiveAgent:
        # Verify base agent exists and user has access
        agent = await self.db.get(AgentProfile, payload.agent_id)
        if not agent:
            raise NotFoundError("Agent", str(payload.agent_id))
        # Ownership check: user must own agent or agent is template/marketplace
        if agent.user_id != user_id and not agent.is_template and not agent.marketplace_listed:
            raise NotFoundError("Agent", str(payload.agent_id))

        name = payload.name or f"{agent.name} - Active {datetime.now(UTC).strftime('%H%M')}"
        org_id = payload.organization_id or organization_id or agent.organization_id

        # Validate mode & cron
        if payload.mode == ActiveAgentMode.SCHEDULED and not payload.cron_schedule:
            raise ValidationError("cron_schedule required for scheduled mode")

        active = ActiveAgent(
            name=name,
            agent_id=payload.agent_id,
            user_id=user_id,
            organization_id=org_id,
            status=ActiveAgentStatus.IDLE,
            mode=payload.mode,
            config=payload.config or {},
            cron_schedule=payload.cron_schedule,
            is_active=True,
        )
        self.db.add(active)
        await self.db.flush()
        await self.db.refresh(active)

        await self._log(
            active.id,
            agent.id,
            user_id,
            level="info",
            event_type="created",
            message=f"Active agent '{name}' created in mode {payload.mode}",
            data={"agent_id": str(agent.id), "mode": payload.mode},
        )
        await self.db.commit()
        return active

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID | None = None,
        active_only: bool = False,
        status: str | None = None,
    ) -> list[ActiveAgent]:
        query = select(ActiveAgent).where(ActiveAgent.user_id == user_id)
        if organization_id:
            query = query.where(ActiveAgent.organization_id == organization_id)
        if active_only:
            query = query.where(ActiveAgent.is_active.is_(True))
        if status:
            query = query.where(ActiveAgent.status == status)
        query = query.order_by(ActiveAgent.updated_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all_active(self) -> list[ActiveAgent]:
        """Admin/debug: list all currently running actives across users."""
        result = await self.db.execute(
            select(ActiveAgent).where(
                ActiveAgent.is_active.is_(True),
                ActiveAgent.status.in_(
                    [ActiveAgentStatus.RUNNING, ActiveAgentStatus.IDLE, ActiveAgentStatus.STARTING]
                ),
            )
        )
        return list(result.scalars().all())

    async def get(self, active_id: uuid.UUID, user_id: uuid.UUID | None = None) -> ActiveAgent:
        active = await self.db.get(ActiveAgent, active_id)
        if not active:
            raise NotFoundError("ActiveAgent", str(active_id))
        if user_id and active.user_id != user_id:
            raise NotFoundError("ActiveAgent", str(active_id))
        return active

    async def update(
        self, active_id: uuid.UUID, user_id: uuid.UUID, payload: dict
    ) -> ActiveAgent:
        active = await self.get(active_id, user_id)
        for field in ("name", "config", "cron_schedule"):
            if field in payload and payload[field] is not None:
                setattr(active, field, payload[field])
        await self.db.flush()
        await self._log(
            active.id,
            active.agent_id,
            active.user_id,
            level="info",
            event_type="updated",
            message=f"Active agent '{active.name}' updated",
            data=payload,
        )
        await self.db.commit()
        await self.db.refresh(active)
        return active

    # ─── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self, active_id: uuid.UUID, user_id: uuid.UUID) -> ActiveAgent:
        lock = _get_lock(active_id)
        async with lock:
            active = await self.get(active_id, user_id)
            if active.status in (ActiveAgentStatus.RUNNING, ActiveAgentStatus.STARTING):
                return active  # already running

            active.status = ActiveAgentStatus.STARTING
            active.started_at = datetime.now(UTC)
            active.heartbeat_at = datetime.now(UTC)
            active.last_error = None
            await self.db.flush()

            await self._log(
                active.id,
                active.agent_id,
                active.user_id,
                level="info",
                event_type="starting",
                message=f"Starting active agent {active.name}",
            )
            await self.db.commit()

            # Start in-memory loop (if not already)
            if active.id not in _running_loops or _running_loops[active.id].done():
                # Import here to avoid circular
                task = asyncio.create_task(self._run_loop(active.id))
                _running_loops[active.id] = task
                logger.info(f"Started loop for {active.id}")

            active.status = ActiveAgentStatus.RUNNING
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(active)
            return active

    async def stop(self, active_id: uuid.UUID, user_id: uuid.UUID) -> ActiveAgent:
        lock = _get_lock(active_id)
        async with lock:
            active = await self.get(active_id, user_id)
            active.status = ActiveAgentStatus.STOPPING
            await self.db.flush()

            # Cancel loop
            loop_task = _running_loops.pop(active.id, None)
            if loop_task:
                loop_task.cancel()
                try:
                    await loop_task
                except asyncio.CancelledError:
                    pass

            active.status = ActiveAgentStatus.STOPPED
            active.stopped_at = datetime.now(UTC)
            active.is_active = False
            await self.db.flush()

            await self._log(
                active.id,
                active.agent_id,
                active.user_id,
                level="info",
                event_type="stopped",
                message=f"Stopped active agent {active.name}",
            )
            await self.db.commit()
            await self.db.refresh(active)
            return active

    async def pause(self, active_id: uuid.UUID, user_id: uuid.UUID) -> ActiveAgent:
        active = await self.get(active_id, user_id)
        if active.status != ActiveAgentStatus.RUNNING:
            raise ValidationError(f"Cannot pause agent in status {active.status}")
        active.status = ActiveAgentStatus.PAUSED
        active.paused_at = datetime.now(UTC)
        await self.db.flush()
        await self._log(
            active.id,
            active.agent_id,
            active.user_id,
            level="info",
            event_type="paused",
            message=f"Paused active agent {active.name}",
        )
        await self.db.commit()
        await self.db.refresh(active)
        return active

    async def resume(self, active_id: uuid.UUID, user_id: uuid.UUID) -> ActiveAgent:
        active = await self.get(active_id, user_id)
        if active.status != ActiveAgentStatus.PAUSED:
            raise ValidationError(f"Cannot resume agent in status {active.status}")
        active.status = ActiveAgentStatus.RUNNING
        active.heartbeat_at = datetime.now(UTC)
        await self.db.flush()
        await self._log(
            active.id,
            active.agent_id,
            active.user_id,
            level="info",
            event_type="resumed",
            message=f"Resumed active agent {active.name}",
        )
        await self.db.commit()

        # Ensure loop running
        if active.id not in _running_loops or _running_loops[active.id].done():
            task = asyncio.create_task(self._run_loop(active.id))
            _running_loops[active.id] = task

        await self.db.refresh(active)
        return active

    async def heartbeat(self, active_id: uuid.UUID, message: str | None = None) -> ActiveAgent:
        active = await self.db.get(ActiveAgent, active_id)
        if not active:
            raise NotFoundError("ActiveAgent", str(active_id))
        active.heartbeat_at = datetime.now(UTC)
        if message:
            await self._log(
                active.id,
                active.agent_id,
                active.user_id,
                level="debug",
                event_type="heartbeat",
                message=message,
            )
        await self.db.flush()
        await self.db.commit()
        return active

    # ─── Task handling ──────────────────────────────────────────────────────

    async def assign_task(
        self,
        active_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        priority: int = 1,
        input_data: dict | None = None,
    ) -> AgentTask:
        active = await self.get(active_id, user_id)
        if active.status not in (ActiveAgentStatus.RUNNING, ActiveAgentStatus.IDLE):
            raise ValidationError(f"Cannot assign task to agent in status {active.status}")

        task = AgentTask(
            title=title,
            description=description,
            priority=priority,
            input_data=input_data or {},
            agent_id=active.agent_id,
            user_id=active.user_id,
            status="pending",
        )
        self.db.add(task)
        await self.db.flush()

        # Optionally set as current task to prioritize
        active.current_task_id = task.id
        await self.db.flush()

        await self._log(
            active.id,
            active.agent_id,
            active.user_id,
            level="info",
            event_type="task_assigned",
            message=f"Task '{title}' assigned to {active.name}",
            data={"task_id": str(task.id), "title": title},
        )
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_logs(
        self,
        active_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 100,
        level: str | None = None,
        event_type: str | None = None,
    ) -> list[ActiveAgentLog]:
        active = await self.get(active_id, user_id)
        query = (
            select(ActiveAgentLog)
            .where(ActiveAgentLog.active_agent_id == active.id)
            .order_by(ActiveAgentLog.created_at.desc())
            .limit(limit)
        )
        if level:
            query = query.where(ActiveAgentLog.level == level)
        if event_type:
            query = query.where(ActiveAgentLog.event_type == event_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stats(self, user_id: uuid.UUID, organization_id: uuid.UUID | None = None) -> dict:
        base_query = select(ActiveAgent).where(ActiveAgent.user_id == user_id)
        if organization_id:
            base_query = base_query.where(ActiveAgent.organization_id == organization_id)

        all_active = (await self.db.execute(base_query)).scalars().all()

        total_runs = sum(a.run_count for a in all_active)
        total_completed = sum(a.total_tasks_completed for a in all_active)

        return {
            "total_active": len(all_active),
            "running": len([a for a in all_active if a.status == ActiveAgentStatus.RUNNING]),
            "idle": len([a for a in all_active if a.status == ActiveAgentStatus.IDLE]),
            "paused": len([a for a in all_active if a.status == ActiveAgentStatus.PAUSED]),
            "error": len([a for a in all_active if a.status == ActiveAgentStatus.ERROR]),
            "total_runs": total_runs,
            "total_tasks_completed": total_completed,
        }

    # ─── Internal helpers ───────────────────────────────────────────────────

    async def _log(
        self,
        active_agent_id: uuid.UUID,
        agent_id: uuid.UUID,
        user_id: uuid.UUID,
        level: str = "info",
        event_type: str = "log",
        message: str = "",
        data: dict | None = None,
    ):
        log = ActiveAgentLog(
            active_agent_id=active_agent_id,
            agent_id=agent_id,
            user_id=user_id,
            level=level,
            event_type=event_type,
            message=message,
            data=data or {},
        )
        self.db.add(log)
        # Flush but don't commit here necessarily; caller will commit
        try:
            await self.db.flush()
        except Exception:
            # If flush fails, ignore (might be in different session)
            pass

    async def _run_loop(self, active_id: uuid.UUID):
        """
        Main loop for an active agent. Runs until status != RUNNING or cancelled.

        This is a simplified autonomous loop:
        - heartbeat every 10s
        - check for pending tasks
        - if task found, execute via AgentOrchestrator
        - sleep briefly

        In production, this would be executed by Celery beat workers.
        """
        logger.info(f"ActiveAgent loop starting for {active_id}")
        try:
            # We need a new DB session for the loop since we are in background task
            # Import here to avoid circular
            from app.main import async_session_factory

            while True:
                async with async_session_factory() as session:
                    # Load active agent fresh
                    active = await session.get(ActiveAgent, active_id)
                    if not active:
                        logger.info(f"ActiveAgent {active_id} not found, ending loop")
                        break
                    if active.status not in (
                        ActiveAgentStatus.RUNNING,
                        ActiveAgentStatus.IDLE,
                        ActiveAgentStatus.STARTING,
                    ):
                        logger.info(
                            f"ActiveAgent {active_id} status {active.status}, ending loop"
                        )
                        break

                    # Heartbeat
                    active.heartbeat_at = datetime.now(UTC)
                    await session.flush()

                    # Try to find a pending task for this agent
                    pending_task = await self._find_pending_task(session, active)

                    if pending_task:
                        # Mark as running
                        active.current_task_id = pending_task.id
                        active.status = ActiveAgentStatus.RUNNING
                        await session.flush()
                        await session.commit()

                        # Log task start
                        log = ActiveAgentLog(
                            active_agent_id=active.id,
                            agent_id=active.agent_id,
                            user_id=active.user_id,
                            level="info",
                            event_type="task_start",
                            message=f"Starting task: {pending_task.title}",
                            data={"task_id": str(pending_task.id)},
                        )
                        session.add(log)
                        await session.commit()

                        # Execute task via orchestrator
                        try:
                            from app.services.agent_service import AgentOrchestrator

                            orchestrator = AgentOrchestrator(session)
                            # Execute
                            result = await orchestrator.execute_task(
                                active.agent_id, pending_task.id, active.user_id
                            )

                            # Update active stats
                            active.total_tasks_completed += 1
                            active.run_count += 1
                            active.total_tokens_used += result.__dict__.get("tokens_used", 0) if hasattr(result, "__dict__") else 0
                            active.current_task_id = None
                            active.status = ActiveAgentStatus.IDLE

                            # ─── Skill training on success ───
                            try:
                                from sqlalchemy import select as sel

                                from app.models.agent import AgentSkill
                                from app.services.skill_library import calculate_skill_xp_gain

                                # Find a skill related to task or random
                                skill_result = await session.execute(
                                    sel(AgentSkill).where(AgentSkill.agent_id == active.agent_id).order_by(AgentSkill.proficiency.asc()).limit(3)
                                )
                                low_skills = skill_result.scalars().all()
                                if low_skills:
                                    for sk in low_skills[:1]:  # train lowest proficiency skill
                                        xp = calculate_skill_xp_gain(sk.proficiency, task_complexity=2, success=True)
                                        # 30% chance to level up if low level
                                        import random

                                        if random.random() < max(0.15, (10 - sk.proficiency) / 15) and sk.proficiency < 10:
                                            old = sk.proficiency
                                            sk.proficiency = min(10, sk.proficiency + 1)
                                            # Log level up
                                            lvl_log = ActiveAgentLog(
                                                active_agent_id=active.id,
                                                agent_id=active.agent_id,
                                                user_id=active.user_id,
                                                level="info",
                                                event_type="skill_level_up",
                                                message=f"Skill '{sk.name}' leveled up {old} -> {sk.proficiency} (+{xp} XP) 🎉",
                                                data={"skill": sk.name, "old": old, "new": sk.proficiency, "xp": xp},
                                            )
                                            session.add(lvl_log)
                            except Exception as se:
                                logger.warning(f"Skill training failed: {se}")

                            # Log completion
                            log_done = ActiveAgentLog(
                                active_agent_id=active.id,
                                agent_id=active.agent_id,
                                user_id=active.user_id,
                                level="info",
                                event_type="task_complete",
                                message=f"Completed task: {pending_task.title}",
                                data={"task_id": str(pending_task.id), "result": str(result.result)[:500] if result.result else ""},
                            )
                            session.add(log_done)
                            await session.commit()

                        except Exception as e:
                            logger.error(
                                f"Task execution failed for active agent {active_id}: {e}",
                                exc_info=True,
                            )
                            active.last_error = str(e)[:1000]
                            active.status = ActiveAgentStatus.ERROR

                            log_err = ActiveAgentLog(
                                active_agent_id=active.id,
                                agent_id=active.agent_id,
                                user_id=active.user_id,
                                level="error",
                                event_type="task_error",
                                message=f"Task failed: {str(e)[:500]}",
                                data={"task_id": str(pending_task.id), "error": str(e)[:1000]},
                            )
                            session.add(log_err)
                            await session.commit()

                            # Backoff on error
                            await asyncio.sleep(5)
                    else:
                        # No tasks, go idle
                        if active.status == ActiveAgentStatus.RUNNING:
                            active.status = ActiveAgentStatus.IDLE
                            await session.commit()

                # Sleep before next iteration - different per mode
                # For continuous, short sleep; scheduled checked via cron logic omitted for brevity
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info(f"ActiveAgent loop cancelled for {active_id}")
            # Mark as stopped if needed? Let caller handle
            raise
        except Exception as e:
            logger.error(f"ActiveAgent loop crashed for {active_id}: {e}", exc_info=True)
            # Try to mark error status
            try:
                from app.main import async_session_factory

                async with async_session_factory() as session:
                    active = await session.get(ActiveAgent, active_id)
                    if active:
                        active.status = ActiveAgentStatus.ERROR
                        active.last_error = str(e)[:1000]
                        log = ActiveAgentLog(
                            active_agent_id=active.id,
                            agent_id=active.agent_id,
                            user_id=active.user_id,
                            level="error",
                            event_type="loop_crash",
                            message=f"Loop crashed: {str(e)[:500]}",
                            data={"error": str(e)[:1000]},
                        )
                        session.add(log)
                        await session.commit()
            except Exception:
                pass
        finally:
            # Cleanup registry
            _running_loops.pop(active_id, None)
            logger.info(f"ActiveAgent loop ended for {active_id}")

    async def _find_pending_task(
        self, session: AsyncSession, active: ActiveAgent
    ) -> AgentTask | None:
        """Find next pending task for this agent, prioritizing current_task_id."""
        # If active has current_task_id that is still pending, return it
        if active.current_task_id:
            task = await session.get(AgentTask, active.current_task_id)
            if task and task.status in ("pending", "planning", "executing"):
                return task

        # Otherwise find any pending task for this agent
        result = await session.execute(
            select(AgentTask)
            .where(
                AgentTask.agent_id == active.agent_id,
                AgentTask.status.in_(["pending", "planning"]),
            )
            .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()


# Singleton helpers for in-memory registry
def get_active_agent_registry() -> dict[uuid.UUID, asyncio.Task]:
    return _running_loops


async def cleanup_stale_agents(db: AsyncSession, stale_minutes: int = 10):
    """Mark agents as error if heartbeat older than stale_minutes."""
    cutoff = datetime.now(UTC) - timedelta(minutes=stale_minutes)
    result = await db.execute(
        select(ActiveAgent).where(
            ActiveAgent.heartbeat_at < cutoff,
            ActiveAgent.status.in_([ActiveAgentStatus.RUNNING, ActiveAgentStatus.STARTING]),
            ActiveAgent.is_active.is_(True),
        )
    )
    stale = result.scalars().all()
    for agent in stale:
        agent.status = ActiveAgentStatus.ERROR
        agent.last_error = f"No heartbeat since {agent.heartbeat_at}, marked stale"
        log = ActiveAgentLog(
            active_agent_id=agent.id,
            agent_id=agent.agent_id,
            user_id=agent.user_id,
            level="warn",
            event_type="stale_detected",
            message=f"Agent {agent.name} marked stale due to missing heartbeat",
            data={"last_heartbeat": agent.heartbeat_at.isoformat() if agent.heartbeat_at else None},
        )
        db.add(log)
    await db.commit()
    return len(stale)

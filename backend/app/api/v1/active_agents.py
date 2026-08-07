"""
Active AI Agents API - manage running agent instances.

Provides:
- List / create / get / update active agents
- Start / stop / pause / resume lifecycle
- Assign tasks
- Logs & stats
- Heartbeat
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.active_agent import (
    ActiveAgentCreate,
    ActiveAgentLogResponse,
    ActiveAgentResponse,
    ActiveAgentStatsResponse,
    TaskAssignRequest,
)
from app.services.active_agent_service import ActiveAgentService

router = APIRouter()


@router.get("/templates", tags=["Active AI Agents Templates"])
async def list_active_agent_templates(category: str | None = Query(None)):
    from app.services.active_agent_templates import list_templates

    return list_templates(category)


@router.get("/templates/{template_id}", tags=["Active AI Agents Templates"])
async def get_active_agent_template(template_id: str):
    from app.services.active_agent_templates import get_template

    tpl = get_template(template_id)
    if not tpl:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Template", template_id)
    return tpl


@router.post("/", response_model=ActiveAgentResponse)
async def create_active_agent(
    payload: ActiveAgentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    active = await svc.create(current_user.id, payload, organization_id=None)
    # Enrich with agent info
    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.get("/", response_model=list[ActiveAgentResponse])
async def list_active_agents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    organization_id: uuid.UUID | None = Query(None),
    active_only: bool = Query(False),
    status: str | None = Query(None),
):
    svc = ActiveAgentService(db)
    actives = await svc.list_for_user(
        current_user.id,
        organization_id=organization_id,
        active_only=active_only,
        status=status,
    )
    responses = []
    for a in actives:
        responses.append(
            ActiveAgentResponse(
                **{k: getattr(a, k) for k in ActiveAgentResponse.model_fields if hasattr(a, k)},
                agent_name=a.agent.name if a.agent else None,
                agent_role=a.agent.role if a.agent else None,
            )
        )
    return responses


@router.get("/stats", response_model=ActiveAgentStatsResponse)
async def get_active_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    organization_id: uuid.UUID | None = Query(None),
):
    svc = ActiveAgentService(db)
    stats = await svc.get_stats(current_user.id, organization_id)
    return ActiveAgentStatsResponse(**stats)


@router.get("/{active_id}", response_model=ActiveAgentResponse)
async def get_active_agent(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    active = await svc.get(active_id, current_user.id)
    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.patch("/{active_id}", response_model=ActiveAgentResponse)
async def update_active_agent(
    active_id: uuid.UUID,
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    active = await svc.update(active_id, current_user.id, payload)
    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.post("/{active_id}/start", response_model=ActiveAgentResponse)
async def start_active_agent(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    active = await svc.start(active_id, current_user.id)
    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.post("/{active_id}/stop", response_model=ActiveAgentResponse)
async def stop_active_agent(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    active = await svc.stop(active_id, current_user.id)
    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.post("/{active_id}/pause", response_model=ActiveAgentResponse)
async def pause_active_agent(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    active = await svc.pause(active_id, current_user.id)
    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.post("/{active_id}/resume", response_model=ActiveAgentResponse)
async def resume_active_agent(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    active = await svc.resume(active_id, current_user.id)
    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.post("/{active_id}/heartbeat", response_model=ActiveAgentResponse)
async def heartbeat_active_agent(
    active_id: uuid.UUID,
    message: str | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    # Heartbeat may be called by agent itself without user context? Allow without user check for now
    # If current_user is None, we still try to heartbeat via ID only
    from app.models.active_agent import ActiveAgent

    if current_user is not None:
        svc = ActiveAgentService(db)
        # Verify ownership if user provided
        active = await svc.get(active_id, current_user.id)
        await svc.heartbeat(active_id, message)
        # Reload
        active = await svc.get(active_id, current_user.id)
    else:
        # Anonymous heartbeat (agent internal)
        svc = ActiveAgentService(db)  # type: ignore
        # Direct DB access
        active = await db.get(ActiveAgent, active_id)  # type: ignore
        if not active:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("ActiveAgent", str(active_id))
        from datetime import UTC, datetime

        active.heartbeat_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(active)

    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.post("/from-template/{template_id}", response_model=ActiveAgentResponse)
async def create_from_template(
    template_id: str,
    agent_id: uuid.UUID | None = Query(None, description="Base agent profile ID (optional, will auto-create if not provided)"),
    name: str | None = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore
):
    from sqlalchemy import select

    from app.models.active_agent import ActiveAgentMode
    from app.models.agent import AgentProfile
    from app.schemas.active_agent import ActiveAgentCreate
    from app.services.active_agent_templates import get_template

    tpl = get_template(template_id)
    if not tpl:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Template", template_id)

    # If no agent_id provided, auto-create a base AgentProfile from template
    if agent_id is None:
        # Check if user already has an agent from this template to reuse
        existing = await db.execute(
            select(AgentProfile).where(
                AgentProfile.user_id == current_user.id,  # type: ignore
                AgentProfile.name == tpl["name"],
            )
        )
        existing_agent = existing.scalar_one_or_none()
        if existing_agent:
            agent_id = existing_agent.id
        else:
            # Create new agent profile from template
            new_agent = AgentProfile(
                name=tpl["name"],
                role=tpl.get("category", "assistant"),
                description=tpl.get("description", ""),
                system_prompt=tpl.get("system_prompt", ""),
                model="gpt-4o",
                temperature=0.7,
                status="active",
                user_id=current_user.id,  # type: ignore
                config={
                    "template_id": template_id,
                    "tools": tpl.get("tools", []),
                    "skills": tpl.get("skills", []),
                },
            )
            db.add(new_agent)
            await db.flush()
            await db.refresh(new_agent)

            # Create associated skills and tools from template
            from app.models.agent import AgentSkill, AgentTool

            for skill_name in tpl.get("skills", [])[:5]:
                skill = AgentSkill(
                    name=skill_name,
                    description=f"Skill: {skill_name}",
                    category=tpl.get("category"),
                    proficiency=7,
                    agent_id=new_agent.id,
                )
                db.add(skill)

            for tool_type in tpl.get("tools", [])[:5]:
                tool = AgentTool(
                    name=f"{tool_type}_tool",
                    tool_type=tool_type,
                    description=f"Tool for {tool_type}",
                    config={},
                    enabled=True,
                    agent_id=new_agent.id,
                )
                db.add(tool)

            await db.flush()
            agent_id = new_agent.id
            await db.commit()

    mode_str = tpl.get("default_mode", "continuous")
    try:
        mode = ActiveAgentMode(mode_str)
    except ValueError:
        mode = ActiveAgentMode.CONTINUOUS

    payload = ActiveAgentCreate(
        agent_id=agent_id,  # type: ignore
        name=name or f"{tpl['name']} - Active",
        mode=mode,
        config={
            "template_id": template_id,
            "system_prompt_override": tpl.get("system_prompt"),
            "tools": tpl.get("tools", []),
            "skills": tpl.get("skills", []),
        },
        cron_schedule=tpl.get("cron"),
    )

    svc = ActiveAgentService(db)  # type: ignore
    active = await svc.create(current_user.id, payload, organization_id=None)  # type: ignore

    # Auto-start the newly created active agent
    try:
        active = await svc.start(active.id, current_user.id)  # type: ignore
    except Exception:
        pass

    return ActiveAgentResponse(
        **{k: getattr(active, k) for k in ActiveAgentResponse.model_fields if hasattr(active, k)},
        agent_name=active.agent.name if active.agent else None,
        agent_role=active.agent.role if active.agent else None,
    )


@router.post("/{active_id}/tasks")
async def assign_task_to_active_agent(
    active_id: uuid.UUID,
    payload: TaskAssignRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    task = await svc.assign_task(
        active_id,
        current_user.id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        input_data=payload.input_data,
    )
    return {
        "id": str(task.id),
        "title": task.title,
        "status": task.status,
        "agent_id": str(task.agent_id),
        "active_agent_id": str(active_id),
    }


@router.get("/{active_id}/logs", response_model=list[ActiveAgentLogResponse])
async def get_active_agent_logs(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(100, ge=1, le=500),
    level: str | None = Query(None),
    event_type: str | None = Query(None),
):
    svc = ActiveAgentService(db)
    logs = await svc.get_logs(active_id, current_user.id, limit=limit, level=level, event_type=event_type)
    return logs


@router.delete("/{active_id}")
async def delete_active_agent(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentService(db)
    # Stop first if running
    try:
        active = await svc.get(active_id, current_user.id)
        if active.status in ("running", "starting", "idle", "paused"):
            await svc.stop(active_id, current_user.id)
    except Exception:
        pass

    # Delete
    active = await svc.get(active_id, current_user.id)
    await db.delete(active)
    await db.commit()
    return {"message": "Active agent deleted", "id": str(active_id)}


# ─── Goals ──────────────────────────────────────────────────────────────────

@router.post("/{active_id}/goals", response_model=dict)
async def create_goal(
    active_id: uuid.UUID,
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.active_agent import ActiveAgentGoal

    svc = ActiveAgentService(db)
    active = await svc.get(active_id, current_user.id)

    goal = ActiveAgentGoal(
        active_agent_id=active.id,
        agent_id=active.agent_id,
        user_id=active.user_id,
        title=payload.get("title", "Untitled Goal"),
        description=payload.get("description"),
        priority=payload.get("priority", 1),
        success_criteria=payload.get("success_criteria"),
        deadline_at=payload.get("deadline_at"),
    )
    db.add(goal)
    await db.flush()
    await db.commit()
    await db.refresh(goal)

    await svc._log(
        active.id,
        active.agent_id,
        active.user_id,
        level="info",
        event_type="goal_created",
        message=f"Goal created: {goal.title}",
        data={"goal_id": str(goal.id)},
    )
    await db.commit()

    return {
        "id": str(goal.id),
        "title": goal.title,
        "status": goal.status,
        "progress": goal.progress,
    }


@router.get("/{active_id}/goals", response_model=list[dict])
async def list_goals(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from sqlalchemy import select

    from app.models.active_agent import ActiveAgentGoal

    svc = ActiveAgentService(db)
    await svc.get(active_id, current_user.id)

    result = await db.execute(
        select(ActiveAgentGoal)
        .where(ActiveAgentGoal.active_agent_id == active_id)
        .order_by(ActiveAgentGoal.priority.desc(), ActiveAgentGoal.created_at.desc())
    )
    goals = result.scalars().all()
    return [
        {
            "id": str(g.id),
            "title": g.title,
            "description": g.description,
            "status": g.status,
            "priority": g.priority,
            "progress": g.progress,
            "deadline_at": g.deadline_at.isoformat() if g.deadline_at else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in goals
    ]


# ─── Memory ─────────────────────────────────────────────────────────────────

@router.post("/{active_id}/memory", response_model=dict)
async def add_memory(
    active_id: uuid.UUID,
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.active_agent import ActiveAgentMemory

    svc = ActiveAgentService(db)
    active = await svc.get(active_id, current_user.id)

    mem = ActiveAgentMemory(
        active_agent_id=active.id,
        agent_id=active.agent_id,
        user_id=active.user_id,
        key=payload.get("key", f"mem_{uuid.uuid4().hex[:8]}"),
        content=payload.get("content", ""),
        memory_type=payload.get("memory_type", "episodic"),
        importance=payload.get("importance", 1),
    )
    db.add(mem)
    await db.flush()
    await db.commit()
    await db.refresh(mem)

    return {"id": str(mem.id), "key": mem.key, "content": mem.content[:200]}


@router.get("/{active_id}/memory", response_model=list[dict])
async def list_memory(
    active_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=200),
):
    from sqlalchemy import select

    from app.models.active_agent import ActiveAgentMemory

    svc = ActiveAgentService(db)
    await svc.get(active_id, current_user.id)

    result = await db.execute(
        select(ActiveAgentMemory)
        .where(ActiveAgentMemory.active_agent_id == active_id)
        .order_by(ActiveAgentMemory.importance.desc(), ActiveAgentMemory.created_at.desc())
        .limit(limit)
    )
    mems = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "key": m.key,
            "content": m.content,
            "memory_type": m.memory_type,
            "importance": m.importance,
            "access_count": m.access_count,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in mems
    ]

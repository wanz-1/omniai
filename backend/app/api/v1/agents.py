import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.agent import (
    AgentAnalytics,
    AgentExecution,
    AgentMemory,
    AgentProfile,
    AgentSkill,
    AgentTask,
    AgentTool,
    Workflow,
    WorkflowStep,
)
from app.models.user import User
from app.schemas.agent import (
    AgentAnalyticsResponse,
    AgentChatRequest,
    AgentChatResponse,
    AgentCreate,
    AgentResponse,
    AgentTaskCreate,
    AgentTaskResponse,
    AgentUpdate,
    ExecutionResponse,
    MemoryCreate,
    MemoryResponse,
    SkillCreate,
    SkillResponse,
    ToolCreate,
    ToolResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowStepResponse,
)
from app.ws.manager import manager

router = APIRouter()


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
    template: bool | None = None,
    marketplace: bool | None = None,
):
    query = select(AgentProfile).where(AgentProfile.user_id == current_user.id)
    if category:
        query = query.where(AgentProfile.template_category == category)
    if template is not None:
        query = query.where(AgentProfile.is_template == template)
    if marketplace:
        query = query.where(AgentProfile.marketplace_listed.is_(True))
    query = query.order_by(AgentProfile.updated_at.desc())
    result = await db.execute(query)
    agents = result.scalars().all()
    return [await _load_agent_relations(a, db) for a in agents]


@router.post("", response_model=AgentResponse)
async def create_agent(
    body: AgentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = AgentProfile(
        name=body.name,
        role=body.role,
        description=body.description,
        system_prompt=body.system_prompt,
        model=body.model,
        temperature=body.temperature,
        icon=body.icon,
        color=body.color,
        user_id=current_user.id,
    )
    db.add(agent)
    await db.flush()

    for sk in body.skills:
        skill = AgentSkill(agent_id=agent.id, **sk.model_dump())
        db.add(skill)
    for t in body.tools:
        tool = AgentTool(agent_id=agent.id, **t.model_dump())
        db.add(tool)

    analytics = AgentAnalytics(agent_id=agent.id)
    db.add(analytics)
    await db.flush()

    return await _load_agent_relations(agent, db)


@router.get("/templates", response_model=list[AgentResponse])
async def list_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
):
    query = select(AgentProfile).where(AgentProfile.is_template.is_(True))
    if category:
        query = query.where(AgentProfile.template_category == category)
    result = await db.execute(query.order_by(AgentProfile.download_count.desc()))
    agents = result.scalars().all()
    return [await _load_agent_relations(a, db) for a in agents]


@router.get("/marketplace", response_model=list[AgentResponse])
async def list_marketplace(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
):
    query = select(AgentProfile).where(
        AgentProfile.marketplace_listed.is_(True),
        AgentProfile.published.is_(True),
    )
    if category:
        query = query.where(AgentProfile.template_category == category)
    result = await db.execute(query.order_by(AgentProfile.download_count.desc()))
    agents = result.scalars().all()
    return [await _load_agent_relations(a, db) for a in agents]


@router.post("/{agent_id}/clone")
async def clone_agent(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    original = await db.get(AgentProfile, agent_id)
    if not original:
        raise NotFoundError("Agent", str(agent_id))
    if not original.is_template and not original.marketplace_listed and original.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))

    clone = AgentProfile(
        name=f"{original.name} (Copy)",
        role=original.role,
        description=original.description,
        system_prompt=original.system_prompt,
        model=original.model,
        temperature=original.temperature,
        icon=original.icon,
        color=original.color,
        config=original.config,
        user_id=current_user.id,
    )
    db.add(clone)
    await db.flush()

    skills = await db.execute(select(AgentSkill).where(AgentSkill.agent_id == agent_id))
    for s in skills.scalars():
        db.add(AgentSkill(agent_id=clone.id, name=s.name, description=s.description, category=s.category, proficiency=s.proficiency))

    tools = await db.execute(select(AgentTool).where(AgentTool.agent_id == agent_id))
    for t in tools.scalars():
        db.add(AgentTool(agent_id=clone.id, name=t.name, tool_type=t.tool_type, description=t.description, config=t.config))

    analytics = AgentAnalytics(agent_id=clone.id)
    db.add(analytics)
    await db.flush()

    return await _load_agent_relations(clone, db)

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or (agent.user_id != current_user.id and not agent.is_template and not agent.marketplace_listed):
        raise NotFoundError("Agent", str(agent_id))
    return await _load_agent_relations(agent, db)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(agent, field, value)
    await db.flush()
    return await _load_agent_relations(agent, db)


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    await db.delete(agent)
    await db.flush()
    return {"message": "Agent deleted"}


@router.post("/{agent_id}/publish")
async def publish_agent(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    marketplace_listed: bool = False,
    price: float | None = None,
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    agent.published = True
    agent.marketplace_listed = marketplace_listed
    if price is not None:
        agent.price = price
    await db.flush()
    return {"message": "Agent published", "marketplace_listed": marketplace_listed}


@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    agent_id: uuid.UUID,
    body: AgentChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.agent_service import AgentOrchestrator
    orchestrator = AgentOrchestrator(db)
    result = await orchestrator.chat(agent_id, current_user.id, body.message)
    return result


@router.post("/{agent_id}/chat/stream")
async def chat_with_agent_stream(
    agent_id: uuid.UUID,
    body: AgentChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.agent_service import AgentOrchestrator
    orchestrator = AgentOrchestrator(db)

    async def event_generator():
        async for event in orchestrator.chat_stream(agent_id, current_user.id, body.message):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/{agent_id}/tasks", response_model=list[AgentTaskResponse])
async def list_tasks(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    query = select(AgentTask).where(AgentTask.agent_id == agent_id)
    if status:
        query = query.where(AgentTask.status == status)
    result = await db.execute(query.order_by(AgentTask.created_at.desc()))
    return result.scalars().all()


@router.post("/{agent_id}/tasks", response_model=AgentTaskResponse)
async def create_task(
    agent_id: uuid.UUID,
    body: AgentTaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    task = AgentTask(
        agent_id=agent_id,
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        input_data=body.input_data,
    )
    db.add(task)
    await db.flush()
    return task


@router.post("/{agent_id}/tasks/{task_id}/execute", response_model=AgentTaskResponse)
async def execute_task(
    agent_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.agent_service import AgentOrchestrator
    orchestrator = AgentOrchestrator(db)
    result = await orchestrator.execute_task(agent_id, task_id, current_user.id)
    return result


@router.get("/{agent_id}/executions", response_model=list[ExecutionResponse])
async def list_executions(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    result = await db.execute(
        select(AgentExecution)
        .where(AgentExecution.agent_id == agent_id)
        .order_by(AgentExecution.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.get("/{agent_id}/analytics", response_model=AgentAnalyticsResponse)
async def get_analytics(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    analytics = await db.execute(
        select(AgentAnalytics).where(AgentAnalytics.agent_id == agent_id)
    )
    return analytics.scalar_one_or_none() or AgentAnalytics(agent_id=agent_id)


@router.get("/{agent_id}/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    result = await db.execute(
        select(Workflow).where(Workflow.agent_id == agent_id).order_by(Workflow.updated_at.desc())
    )
    workflows = result.scalars().all()
    return [await _load_workflow_steps(w, db) for w in workflows]


@router.post("/{agent_id}/workflows", response_model=WorkflowResponse)
async def create_workflow(
    agent_id: uuid.UUID,
    body: WorkflowCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    workflow = Workflow(
        agent_id=agent_id,
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        trigger_event=body.trigger_event,
        trigger_config=body.trigger_config,
    )
    db.add(workflow)
    await db.flush()
    for _i, step_data in enumerate(body.steps):
        step = WorkflowStep(workflow_id=workflow.id, **step_data.model_dump())
        db.add(step)
    await db.flush()
    return await _load_workflow_steps(workflow, db)


@router.put("/{agent_id}/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    agent_id: uuid.UUID,
    workflow_id: uuid.UUID,
    body: WorkflowCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow or workflow.agent_id != agent_id:
        raise NotFoundError("Workflow", str(workflow_id))
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))

    workflow.name = body.name
    workflow.description = body.description
    workflow.trigger_event = body.trigger_event
    workflow.trigger_config = body.trigger_config

    await db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id))
    for _i, step_data in enumerate(body.steps):
        step = WorkflowStep(workflow_id=workflow.id, **step_data.model_dump())
        db.add(step)
    await db.flush()
    return await _load_workflow_steps(workflow, db)


@router.delete("/{agent_id}/workflows/{workflow_id}")
async def delete_workflow(
    agent_id: uuid.UUID,
    workflow_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow or workflow.agent_id != agent_id:
        raise NotFoundError("Workflow", str(workflow_id))
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    await db.delete(workflow)
    await db.flush()
    return {"message": "Workflow deleted"}


@router.get("/{agent_id}/skills", response_model=list[SkillResponse])
async def list_skills(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id).order_by(AgentSkill.name)
    )
    return result.scalars().all()


@router.post("/{agent_id}/skills", response_model=SkillResponse)
async def add_skill(
    agent_id: uuid.UUID,
    body: SkillCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    skill = AgentSkill(agent_id=agent_id, **body.model_dump())
    db.add(skill)
    await db.flush()
    return skill


@router.delete("/{agent_id}/skills/{skill_id}")
async def delete_skill(
    agent_id: uuid.UUID,
    skill_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    skill = await db.get(AgentSkill, skill_id)
    if not skill or skill.agent_id != agent_id:
        raise NotFoundError("Skill", str(skill_id))
    await db.delete(skill)
    await db.flush()
    return {"message": "Skill deleted"}


@router.get("/{agent_id}/tools", response_model=list[ToolResponse])
async def list_tools(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentTool).where(AgentTool.agent_id == agent_id).order_by(AgentTool.name)
    )
    return result.scalars().all()


@router.post("/{agent_id}/tools", response_model=ToolResponse)
async def add_tool(
    agent_id: uuid.UUID,
    body: ToolCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    tool = AgentTool(agent_id=agent_id, **body.model_dump())
    db.add(tool)
    await db.flush()
    return tool


@router.delete("/{agent_id}/tools/{tool_id}")
async def delete_tool(
    agent_id: uuid.UUID,
    tool_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tool = await db.get(AgentTool, tool_id)
    if not tool or tool.agent_id != agent_id:
        raise NotFoundError("Tool", str(tool_id))
    await db.delete(tool)
    await db.flush()
    return {"message": "Tool deleted"}


@router.get("/{agent_id}/memories", response_model=list[MemoryResponse])
async def list_memories(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    memory_type: str | None = None,
    category: str | None = None,
):
    query = select(AgentMemory).where(AgentMemory.agent_id == agent_id)
    if memory_type:
        query = query.where(AgentMemory.memory_type == memory_type)
    if category:
        query = query.where(AgentMemory.category == category)
    result = await db.execute(query.order_by(AgentMemory.importance.desc(), AgentMemory.updated_at.desc()))
    return result.scalars().all()


@router.post("/{agent_id}/memories", response_model=MemoryResponse)
async def add_memory(
    agent_id: uuid.UUID,
    body: MemoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    memory = AgentMemory(
        agent_id=agent_id,
        user_id=current_user.id,
        **body.model_dump(),
    )
    db.add(memory)
    await db.flush()
    return memory


@router.delete("/{agent_id}/memories/{memory_id}")
async def delete_memory(
    agent_id: uuid.UUID,
    memory_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    memory = await db.get(AgentMemory, memory_id)
    if not memory or memory.agent_id != agent_id:
        raise NotFoundError("Memory", str(memory_id))
    await db.delete(memory)
    await db.flush()
    return {"message": "Memory deleted"}


@router.delete("/{agent_id}/memories")
async def clear_memories(
    agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await db.get(AgentProfile, agent_id)
    if not agent or agent.user_id != current_user.id:
        raise NotFoundError("Agent", str(agent_id))
    await db.execute(delete(AgentMemory).where(AgentMemory.agent_id == agent_id))
    await db.flush()
    return {"message": "All memories cleared"}


@router.websocket("/{agent_id}/ws")
async def agent_websocket(
    agent_id: uuid.UUID,
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await manager.connect(websocket, f"agent:{agent_id}")
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "chat":
                from app.services.agent_service import AgentOrchestrator
                orchestrator = AgentOrchestrator(db)
                async for event in orchestrator.chat_stream(
                    agent_id, uuid.UUID(int=0), data.get("content", "")
                ):
                    await websocket.send_json(event)
                await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"agent:{agent_id}")


async def _load_agent_relations(agent: AgentProfile, db: AsyncSession) -> AgentResponse:
    skills_result = await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent.id).order_by(AgentSkill.name)
    )
    tools_result = await db.execute(
        select(AgentTool).where(AgentTool.agent_id == agent.id).order_by(AgentTool.name)
    )
    workflows_result = await db.execute(
        select(Workflow).where(Workflow.agent_id == agent.id).order_by(Workflow.updated_at.desc())
    )
    workflows = []
    for w in workflows_result.scalars():
        steps_result = await db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_id == w.id).order_by(WorkflowStep.order)
        )
        workflows.append(WorkflowResponse(
            id=w.id, name=w.name, description=w.description, is_active=w.is_active,
            trigger_event=w.trigger_event, trigger_config=w.trigger_config,
            agent_id=w.agent_id,
            steps=[WorkflowStepResponse.model_validate(s) for s in steps_result.scalars()],
            created_at=w.created_at, updated_at=w.updated_at,
        ))
    return AgentResponse(
        id=agent.id, name=agent.name, role=agent.role, description=agent.description,
        system_prompt=agent.system_prompt, model=agent.model, temperature=agent.temperature,
        status=agent.status, is_template=agent.is_template, template_category=agent.template_category,
        icon=agent.icon, color=agent.color, config=agent.config,
        published=agent.published, marketplace_listed=agent.marketplace_listed,
        price=agent.price, download_count=agent.download_count,
        user_id=agent.user_id,
        skills=[SkillResponse.model_validate(s) for s in skills_result.scalars()],
        tools=[ToolResponse.model_validate(t) for t in tools_result.scalars()],
        workflows=workflows,
        created_at=agent.created_at, updated_at=agent.updated_at,
    )


async def _load_workflow_steps(workflow: Workflow, db: AsyncSession) -> WorkflowResponse:
    steps_result = await db.execute(
        select(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id).order_by(WorkflowStep.order)
    )
    return WorkflowResponse(
        id=workflow.id, name=workflow.name, description=workflow.description,
        is_active=workflow.is_active, trigger_event=workflow.trigger_event,
        trigger_config=workflow.trigger_config, agent_id=workflow.agent_id,
        steps=[WorkflowStepResponse.model_validate(s) for s in steps_result.scalars()],
        created_at=workflow.created_at, updated_at=workflow.updated_at,
    )

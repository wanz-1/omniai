import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.core.dependencies import get_db
from app.models.agent_network import (
    AgentPerformance,
    AgentTaskDelegation,
    AgentTeam,
    AgentTeamMember,
    AutonomousResearch,
    DevProject,
)
from app.models.user import User
from app.schemas.agent_network import (
    AgentReviewCreate,
    AgentReviewResponse,
    AgentTaskDelegationCreate,
    AgentTaskDelegationResponse,
    AgentTeamCreate,
    AgentTeamMemberAdd,
    AgentTeamResponse,
    DevProjectRequest,
    DevProjectResponse,
    MemoryNetworkCreate,
    MemoryNetworkResponse,
    OrchestrateRequest,
    OrchestrateResponse,
    PermissionCreate,
    PermissionResponse,
    ResearchRequest,
    ResearchResponse,
)
from app.services.agent_communication import AgentCommunicationService
from app.services.agent_evaluation import AgentEvaluationService
from app.services.agent_governance import AgentGovernanceService
from app.services.agent_memory_network import AgentMemoryNetworkService
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.autonomous_research import AutonomousResearchService
from app.services.ai_dev_team import AIDevTeamService

router = APIRouter()


# ─── Orchestration ───────────────────────────────────────────────────────────

@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate_task(
    req: OrchestrateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orchestrator = AgentOrchestrator(db)
    plan = await orchestrator.create_plan(req.task, req.team_config)
    result = await orchestrator.execute_plan(plan, req.task, current_user.id, req.organization_id)
    return OrchestrateResponse(
        final_output=result["final_output"],
        steps_completed=result["steps_completed"],
        agents_involved=result["agents_involved"],
        execution_log=result["execution_log"],
    )


# ─── Teams ───────────────────────────────────────────────────────────────────

@router.post("/teams", response_model=AgentTeamResponse)
async def create_team(
    req: AgentTeamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = AgentTeam(
        name=req.name,
        description=req.description,
        purpose=req.purpose,
        icon=req.icon,
        color=req.color,
        config=req.config or {},
        user_id=current_user.id,
        organization_id=req.organization_id,
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@router.get("/teams", response_model=list[AgentTeamResponse])
async def list_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_id: uuid.UUID | None = None,
):
    stmt = select(AgentTeam).options(selectinload(AgentTeam.members))
    if organization_id:
        stmt = stmt.where(AgentTeam.organization_id == organization_id)
    else:
        stmt = stmt.where(AgentTeam.user_id == current_user.id)
    stmt = stmt.order_by(AgentTeam.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/teams/{team_id}", response_model=AgentTeamResponse)
async def get_team(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentTeam).options(selectinload(AgentTeam.members)).where(AgentTeam.id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    return team


@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: uuid.UUID,
    req: AgentTeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = AgentTeamMember(
        team_id=team_id,
        agent_id=req.agent_id,
        role=req.role,
        responsibilities=req.responsibilities,
        is_lead=req.is_lead,
        order=req.order,
    )
    db.add(member)
    await db.commit()
    return {"message": "Member added", "id": member.id}


@router.delete("/teams/{team_id}/members/{member_id}")
async def remove_team_member(
    team_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentTeamMember).where(AgentTeamMember.id == member_id, AgentTeamMember.team_id == team_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")
    await db.delete(member)
    await db.commit()
    return {"message": "Member removed"}


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AgentTeam).where(AgentTeam.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    await db.delete(team)
    await db.commit()
    return {"message": "Team deleted"}


@router.post("/teams/auto-create")
async def auto_create_team(
    req: OrchestrateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orchestrator = AgentOrchestrator(db)
    roles = req.team_config.get("roles", ["project_manager", "developer", "qa_engineer"]) if req.team_config else ["project_manager", "developer", "qa_engineer"]
    team = await orchestrator.create_team(req.task, req.task, roles, current_user.id, req.organization_id)
    return {"message": "Team created", "team_id": team.id, "name": team.name}


# ─── Inter-Agent Communication ───────────────────────────────────────────────

@router.post("/messages")
async def send_message(
    receiver_id: uuid.UUID,
    content: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    message_type: str = "direct",
    task_id: uuid.UUID | None = None,
    team_id: uuid.UUID | None = None,
):
    svc = AgentCommunicationService(db)
    msg = await svc.send_message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        message_type=message_type,
        task_id=task_id,
        team_id=team_id,
    )
    return {"message": "Sent", "id": msg.id}


@router.get("/messages/{agent_id_1}/{agent_id_2}")
async def get_conversation(
    agent_id_1: uuid.UUID,
    agent_id_2: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    svc = AgentCommunicationService(db)
    messages = await svc.get_conversation(agent_id_1, agent_id_2, limit)
    return messages


@router.get("/messages/team/{team_id}")
async def get_team_messages(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    svc = AgentCommunicationService(db)
    messages = await svc.get_team_messages(team_id, limit)
    return messages


# ─── Task Delegation ─────────────────────────────────────────────────────────

@router.post("/delegations", response_model=AgentTaskDelegationResponse)
async def create_delegation(
    req: AgentTaskDelegationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    delegation = AgentTaskDelegation(
        title=req.title,
        description=req.description,
        priority=req.priority,
        deadline=req.deadline,
        input_data=req.input_data or {},
        assignor_id=current_user.id,
        assignee_id=req.assignee_id,
        team_id=req.team_id,
        parent_task_id=req.parent_task_id,
    )
    db.add(delegation)
    await db.commit()
    await db.refresh(delegation)
    return delegation


@router.get("/delegations", response_model=list[AgentTaskDelegationResponse])
async def list_delegations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    team_id: uuid.UUID | None = None,
    status: str | None = None,
):
    stmt = select(AgentTaskDelegation)
    if team_id:
        stmt = stmt.where(AgentTaskDelegation.team_id == team_id)
    if status:
        stmt = stmt.where(AgentTaskDelegation.status == status)
    stmt = stmt.order_by(AgentTaskDelegation.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/delegations/{delegation_id}/complete")
async def complete_delegation(
    delegation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    output_data: dict | None = None,
    result_summary: str | None = None,
):
    result = await db.execute(select(AgentTaskDelegation).where(AgentTaskDelegation.id == delegation_id))
    delegation = result.scalar_one_or_none()
    if not delegation:
        raise HTTPException(404, "Delegation not found")
    delegation.status = "completed"
    delegation.progress = 100.0
    delegation.output_data = output_data
    delegation.result_summary = result_summary
    delegation.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return delegation


# ─── Memory Network ──────────────────────────────────────────────────────────

@router.post("/memory", response_model=MemoryNetworkResponse)
async def store_memory(
    req: MemoryNetworkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AgentMemoryNetworkService(db)
    entry = await svc.store(
        key=req.key,
        content=req.content,
        memory_type=req.memory_type,
        category=req.category,
        importance=req.importance,
        visibility=req.visibility,
        source=req.source,
        team_id=req.team_id,
        organization_id=req.organization_id,
        agent_id=req.agent_id,
        user_id=current_user.id,
    )
    return entry


@router.get("/memory/search", response_model=list[MemoryNetworkResponse])
async def search_memory(
    query_text: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    team_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
):
    svc = AgentMemoryNetworkService(db)
    memories = await svc.search(query_text, team_id, organization_id)
    return memories


@router.get("/memory/team/{team_id}", response_model=list[MemoryNetworkResponse])
async def get_team_memory(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AgentMemoryNetworkService(db)
    return await svc.get_team_memory(team_id)


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AgentMemoryNetworkService(db)
    deleted = await svc.delete(memory_id)
    if not deleted:
        raise HTTPException(404, "Memory not found")
    return {"message": "Memory deleted"}


# ─── Evaluation & Reviews ────────────────────────────────────────────────────

@router.post("/reviews", response_model=AgentReviewResponse)
async def create_review(
    req: AgentReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    evals = AgentEvaluationService(db)
    review = await evals.review_output(
        reviewer_id=current_user.id,
        reviewee_id=req.reviewee_id,
        content_to_review=req.content or "",
        task_id=req.task_id,
        criteria=req.criteria_scores,
    )
    return review


@router.get("/reviews/{agent_id}", response_model=list[AgentReviewResponse])
async def get_agent_reviews(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    evals = AgentEvaluationService(db)
    return await evals.get_agent_reviews(agent_id)


@router.get("/performance/{agent_id}")
async def get_agent_performance(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    evals = AgentEvaluationService(db)
    perf = await evals.get_performance(agent_id)
    if not perf:
        return {"agent_id": str(agent_id), "total_tasks": 0, "avg_score": None}
    return perf


# ─── Governance & Permissions ────────────────────────────────────────────────

@router.post("/permissions", response_model=PermissionResponse)
async def grant_permission(
    req: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gov = AgentGovernanceService(db)
    perm = await gov.grant_permission(
        agent_id=req.agent_id,
        resource=req.resource,
        action=req.action,
        access_level=req.access_level,
        conditions=req.conditions,
        granted_by=current_user.id,
        team_id=req.team_id,
    )
    return perm


@router.get("/permissions/agent/{agent_id}", response_model=list[PermissionResponse])
async def get_agent_permissions(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gov = AgentGovernanceService(db)
    return await gov.get_agent_permissions(agent_id)


@router.delete("/permissions/{permission_id}")
async def revoke_permission(
    permission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gov = AgentGovernanceService(db)
    revoked = await gov.revoke_permission(permission_id)
    if not revoked:
        raise HTTPException(404, "Permission not found")
    return {"message": "Permission revoked"}


@router.get("/permissions/check/{agent_id}/{resource}/{action}")
async def check_permission(
    agent_id: uuid.UUID,
    resource: str,
    action: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gov = AgentGovernanceService(db)
    allowed = await gov.check_permission(agent_id, resource, action)
    return {"allowed": allowed}


# ─── Autonomous Research ─────────────────────────────────────────────────────

@router.post("/research", response_model=ResearchResponse)
async def conduct_research(
    req: ResearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AutonomousResearchService(db)
    research = await svc.conduct_research(
        title=req.title,
        topic=req.topic,
        depth=req.depth,
        user_id=current_user.id,
        organization_id=req.organization_id,
        context=req.context,
    )
    return research


@router.get("/research", response_model=list[ResearchResponse])
async def list_research(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AutonomousResearchService(db)
    return await svc.list_research(current_user.id)


@router.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(
    research_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AutonomousResearchService(db)
    research = await svc.get_research(research_id)
    if not research:
        raise HTTPException(404, "Research not found")
    return research


# ─── AI Software Development Team ─────────────────────────────────────────────

@router.post("/dev-projects", response_model=DevProjectResponse)
async def create_dev_project(
    req: DevProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AIDevTeamService(db)
    project = await svc.create_project(
        name=req.name,
        description=req.description,
        tech_stack=req.tech_stack,
        requirements_text=req.requirements,
        user_id=current_user.id,
        organization_id=req.organization_id,
    )
    return project


@router.get("/dev-projects", response_model=list[DevProjectResponse])
async def list_dev_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_id: uuid.UUID | None = None,
):
    stmt = select(DevProject).order_by(DevProject.created_at.desc())
    if organization_id:
        stmt = stmt.where(DevProject.organization_id == organization_id)
    else:
        stmt = stmt.where(DevProject.user_id == current_user.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/dev-projects/{project_id}", response_model=DevProjectResponse)
async def get_dev_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DevProject).where(DevProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Dev project not found")
    return project


@router.post("/dev-projects/{project_id}/generate-code")
async def generate_project_code(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AIDevTeamService(db)
    code = await svc.generate_code(project_id)
    return {"message": "Code generated", "files": list(code.keys())}


@router.post("/dev-projects/{project_id}/security-review")
async def security_review_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AIDevTeamService(db)
    review = await svc.run_security_review(project_id)
    return review


@router.post("/dev-projects/{project_id}/run-tests")
async def test_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AIDevTeamService(db)
    tests = await svc.run_tests(project_id)
    return tests


@router.post("/dev-projects/{project_id}/complete")
async def complete_dev_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AIDevTeamService(db)
    project = await svc.complete_project(project_id)
    return {"message": "Project completed", "status": project.status}


# ─── Agent Performance Dashboard ─────────────────────────────────────────────

@router.get("/dashboard/{organization_id}")
async def get_agent_network_dashboard(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    teams_result = await db.execute(
        select(AgentTeam).where(AgentTeam.organization_id == organization_id)
    )
    teams = list(teams_result.scalars().all())

    tasks_result = await db.execute(
        select(AgentTaskDelegation)
        .order_by(AgentTaskDelegation.created_at.desc())
        .limit(20)
    )
    recent_tasks = list(tasks_result.scalars().all())

    perf_result = await db.execute(
        select(AgentPerformance).order_by(AgentPerformance.avg_score.desc()).limit(10)
    )
    top_agents = list(perf_result.scalars().all())

    research_result = await db.execute(
        select(AutonomousResearch)
        .where(AutonomousResearch.organization_id == organization_id)
        .order_by(AutonomousResearch.created_at.desc())
        .limit(10)
    )
    research = list(research_result.scalars().all())

    dev_result = await db.execute(
        select(DevProject)
        .where(DevProject.organization_id == organization_id)
        .order_by(DevProject.created_at.desc())
        .limit(10)
    )
    dev_projects = list(dev_result.scalars().all())

    return {
        "teams": [{"id": str(t.id), "name": t.name, "purpose": t.purpose, "is_active": t.is_active, "created_at": t.created_at.isoformat() if t.created_at else None} for t in teams],
        "recent_tasks": [{"id": str(t.id), "title": t.title, "status": t.status, "progress": t.progress} for t in recent_tasks],
        "top_agents": [{"agent_id": str(p.agent_id), "avg_score": p.avg_score, "total_tasks": p.total_tasks} for p in top_agents],
        "research_count": len(research),
        "dev_projects_count": len(dev_projects),
        "team_count": len(teams),
    }

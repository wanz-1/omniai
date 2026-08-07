"""
Skills API – library and active agent skill management
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.active_agent_skill_service import ActiveAgentSkillService
from app.services.skill_library import get_skill, list_skills

router = APIRouter()


# ─── Library ────────────────────────────────────────────────────────────────

@router.get("/library")
async def list_skill_library(
    category: str | None = Query(None),
    search: str | None = Query(None),
):

    skills = list_skills(category, search)
    return {
        "count": len(skills),
        "categories": sorted(list(set(s["category"] for s in skills))),
        "skills": skills,
    }


@router.get("/library/{skill_id}")
async def get_skill_from_library(skill_id: str):
    skill = get_skill(skill_id)
    if not skill:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Skill", skill_id)
    return skill


@router.get("/categories")
async def list_skill_categories():
    from app.services.skill_library import SKILL_CATEGORIES, SKILL_LIBRARY

    return {
        "categories": SKILL_CATEGORIES,
        "count_per_category": {
            cat: len([s for s in SKILL_LIBRARY if s["category"] == cat]) for cat in SKILL_CATEGORIES
        },
    }


# ─── Active Agent Skills ────────────────────────────────────────────────────

@router.get("/active-agent/{active_agent_id}")
async def list_active_agent_skills(
    active_agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentSkillService(db)
    skills = await svc.list_agent_skills(active_agent_id, current_user.id)
    return {"active_agent_id": str(active_agent_id), "count": len(skills), "skills": skills}


@router.post("/active-agent/{active_agent_id}")
async def add_skill_to_active_agent(
    active_agent_id: uuid.UUID,
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    payload: { skill_id_or_name: str, proficiency?: int }
    """
    skill_id = payload.get("skill_id") or payload.get("skill_id_or_name") or payload.get("name")
    proficiency = payload.get("proficiency", 5)
    if not skill_id:
        from app.core.exceptions import ValidationError

        raise ValidationError("skill_id or name required")

    svc = ActiveAgentSkillService(db)
    result = await svc.add_skill_to_active_agent(active_agent_id, current_user.id, skill_id, proficiency)
    return result


@router.delete("/active-agent/{active_agent_id}/{skill_name}")
async def remove_skill_from_active_agent(
    active_agent_id: uuid.UUID,
    skill_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ActiveAgentSkillService(db)
    result = await svc.remove_skill(active_agent_id, current_user.id, skill_name)
    return result


@router.post("/active-agent/{active_agent_id}/train")
async def train_active_agent_skill(
    active_agent_id: uuid.UUID,
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    payload: { skill_name: str, task_complexity?: int }
    """
    skill_name = payload.get("skill_name") or payload.get("name")
    complexity = payload.get("task_complexity", 2)
    if not skill_name:
        from app.core.exceptions import ValidationError

        raise ValidationError("skill_name required")

    svc = ActiveAgentSkillService(db)
    result = await svc.train_skill(active_agent_id, current_user.id, skill_name, complexity)
    return result


@router.get("/active-agent/{active_agent_id}/recommend")
async def recommend_skills_for_active_agent(
    active_agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    goal: str | None = Query(None, description="Goal to recommend skills for"),
):
    svc = ActiveAgentSkillService(db)
    recs = await svc.recommend(active_agent_id, current_user.id, goal)
    return {"active_agent_id": str(active_agent_id), "goal": goal, "recommendations": recs}


@router.post("/active-agent/{active_agent_id}/auto-learn")
async def auto_learn_skills(
    active_agent_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Auto-learn: analyzes recent tasks and logs, recommends and auto-adds top 2 skills.
    """
    svc = ActiveAgentSkillService(db)
    # Get current skills
    existing = await svc.list_agent_skills(active_agent_id, current_user.id)

    # Get goals to infer what to learn
    from sqlalchemy import select

    from app.models.active_agent import ActiveAgentGoal

    result = await db.execute(
        select(ActiveAgentGoal).where(ActiveAgentGoal.active_agent_id == active_agent_id).order_by(ActiveAgentGoal.priority.desc()).limit(3)
    )
    goals = result.scalars().all()
    goal_text = " ".join([g.title + " " + (g.description or "") for g in goals]) if goals else ""

    recs = await svc.recommend(active_agent_id, current_user.id, goal_text or None)

    # Auto-add top 2 recommendations if not already present
    added = []
    for rec in recs[:2]:
        try:
            added_skill = await svc.add_skill_to_active_agent(
                active_agent_id, current_user.id, rec["id"], proficiency=3
            )
            added.append(added_skill)
        except Exception:
            continue

    return {
        "message": f"Analyzed {len(existing)} existing skills, {len(goals)} goals. Added {len(added)} new skills.",
        "existing_count": len(existing),
        "recommendations": recs[:5],
        "added": added,
    }

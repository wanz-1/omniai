"""
Active Agent Skill Service – Manage skills for active agents, with XP and leveling.

Active agents gain XP when completing tasks, level up skills, and can learn new skills.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.active_agent import ActiveAgent
from app.models.agent import AgentSkill
from app.services.skill_library import (
    calculate_skill_xp_gain,
    get_skill,
    list_skills,
    recommend_skills,
)


class ActiveAgentSkillService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_library(
        self, category: str | None = None, search: str | None = None
    ) -> list[dict]:
        return list_skills(category, search)

    async def get_skill(self, skill_id: str) -> dict:
        skill = get_skill(skill_id)
        if not skill:
            raise NotFoundError("Skill", skill_id)
        return skill

    async def list_agent_skills(self, active_agent_id: uuid.UUID, user_id: uuid.UUID):
        # Verify active agent ownership and get base agent id
        active = await self.db.get(ActiveAgent, active_agent_id)
        if not active or active.user_id != user_id:
            raise NotFoundError("ActiveAgent", str(active_agent_id))

        result = await self.db.execute(
            select(AgentSkill).where(AgentSkill.agent_id == active.agent_id)
        )
        skills = result.scalars().all()
        # Enrich with library data
        enriched = []
        for s in skills:
            lib = get_skill(s.name.lower().replace(" ", "_")) or {}
            enriched.append(
                {
                    "id": str(s.id),
                    "name": s.name,
                    "description": s.description or lib.get("description", ""),
                    "category": s.category or lib.get("category", "technical"),
                    "proficiency": s.proficiency,
                    "icon": lib.get("icon", "🔧"),
                    "levels": lib.get("levels", {}),
                    "tools": lib.get("tools", []),
                    "agent_id": str(s.agent_id),
                    "active_agent_id": str(active_agent_id),
                }
            )
        return enriched

    async def add_skill_to_active_agent(
        self,
        active_agent_id: uuid.UUID,
        user_id: uuid.UUID,
        skill_id_or_name: str,
        proficiency: int = 5,
    ):
        active = await self.db.get(ActiveAgent, active_agent_id)
        if not active or active.user_id != user_id:
            raise NotFoundError("ActiveAgent", str(active_agent_id))

        lib_skill = get_skill(skill_id_or_name.lower().replace(" ", "_"))
        if not lib_skill:
            # Try fuzzy by name
            for s in list_skills():
                if s["name"].lower() == skill_id_or_name.lower():
                    lib_skill = s
                    break
        if not lib_skill:
            raise NotFoundError("Skill", skill_id_or_name)

        # Check if skill already exists on base agent
        existing = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == active.agent_id,
                AgentSkill.name == lib_skill["name"],
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Agent already has skill {lib_skill['name']}")

        # Check prerequisites
        missing_prereqs = []
        for prereq in lib_skill.get("prerequisites", []):
            prereq_check = await self.db.execute(
                select(AgentSkill).where(
                    AgentSkill.agent_id == active.agent_id,
                    AgentSkill.name.ilike(f"%{prereq}%"),
                )
            )
            if not prereq_check.scalar_one_or_none():
                # Check by id
                prereq_check2 = await self.db.execute(
                    select(AgentSkill).where(
                        AgentSkill.agent_id == active.agent_id,
                        AgentSkill.name == get_skill(prereq).get("name") if get_skill(prereq) else prereq,
                    )
                )
                if not prereq_check2.scalar_one_or_none():
                    missing_prereqs.append(prereq)

        if missing_prereqs:
            # Not blocking, just warning - include in response
            pass

        skill = AgentSkill(
            name=lib_skill["name"],
            description=lib_skill["description"],
            category=lib_skill["category"],
            proficiency=max(1, min(10, proficiency)),
            agent_id=active.agent_id,
        )
        self.db.add(skill)
        await self.db.flush()

        # Log skill addition to active agent log
        from app.models.active_agent import ActiveAgentLog

        log = ActiveAgentLog(
            active_agent_id=active.id,
            agent_id=active.agent_id,
            user_id=user_id,
            level="info",
            event_type="skill_added",
            message=f"Skill '{lib_skill['name']}' added (proficiency {proficiency})",
            data={"skill": lib_skill["name"], "proficiency": proficiency},
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(skill)

        return {
            "id": str(skill.id),
            "name": skill.name,
            "proficiency": skill.proficiency,
            "category": skill.category,
            "icon": lib_skill.get("icon"),
            "missing_prerequisites": missing_prereqs,
        }

    async def train_skill(
        self, active_agent_id: uuid.UUID, user_id: uuid.UUID, skill_name: str, task_complexity: int = 2
    ):
        active = await self.db.get(ActiveAgent, active_agent_id)
        if not active or active.user_id != user_id:
            raise NotFoundError("ActiveAgent", str(active_agent_id))

        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == active.agent_id,
                AgentSkill.name == skill_name,
            )
        )
        skill = result.scalar_one_or_none()
        if not skill:
            # Try ilike
            result = await self.db.execute(
                select(AgentSkill).where(
                    AgentSkill.agent_id == active.agent_id,
                    AgentSkill.name.ilike(f"%{skill_name}%"),
                )
            )
            skill = result.scalar_one_or_none()
        if not skill:
            raise NotFoundError("Skill", skill_name)

        # Simulate XP gain
        old_prof = skill.proficiency
        xp_gain = calculate_skill_xp_gain(old_prof, task_complexity, success=True)

        # Simplified level up: if proficiency <10, 20% chance to level up per training, higher if low level
        import random

        level_up_chance = max(0.1, (10 - old_prof) / 10)
        leveled_up = False
        if random.random() < level_up_chance and old_prof < 10:
            skill.proficiency = min(10, old_prof + 1)
            leveled_up = True

        await self.db.flush()

        from app.models.active_agent import ActiveAgentLog

        log = ActiveAgentLog(
            active_agent_id=active.id,
            agent_id=active.agent_id,
            user_id=user_id,
            level="info",
            event_type="skill_trained",
            message=f"Skill '{skill.name}' trained: +{xp_gain} XP, proficiency {old_prof} -> {skill.proficiency}",
            data={
                "skill": skill.name,
                "old_proficiency": old_prof,
                "new_proficiency": skill.proficiency,
                "xp_gain": xp_gain,
                "leveled_up": leveled_up,
            },
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(skill)

        return {
            "id": str(skill.id),
            "name": skill.name,
            "old_proficiency": old_prof,
            "new_proficiency": skill.proficiency,
            "xp_gain": xp_gain,
            "leveled_up": leveled_up,
            "message": f"Trained {skill.name}: proficiency {old_prof} -> {skill.proficiency}" + (" 🎉 Level up!" if leveled_up else ""),
        }

    async def recommend(
        self, active_agent_id: uuid.UUID, user_id: uuid.UUID, goal: str | None = None
    ):
        active = await self.db.get(ActiveAgent, active_agent_id)
        if not active or active.user_id != user_id:
            raise NotFoundError("ActiveAgent", str(active_agent_id))

        result = await self.db.execute(
            select(AgentSkill).where(AgentSkill.agent_id == active.agent_id)
        )
        current_skills = [s.name for s in result.scalars().all()]

        recs = recommend_skills(current_skills, goal)
        return recs

    async def remove_skill(
        self, active_agent_id: uuid.UUID, user_id: uuid.UUID, skill_name: str
    ):
        active = await self.db.get(ActiveAgent, active_agent_id)
        if not active or active.user_id != user_id:
            raise NotFoundError("ActiveAgent", str(active_agent_id))

        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == active.agent_id,
                AgentSkill.name == skill_name,
            )
        )
        skill = result.scalar_one_or_none()
        if not skill:
            result = await self.db.execute(
                select(AgentSkill).where(
                    AgentSkill.agent_id == active.agent_id,
                    AgentSkill.name.ilike(f"%{skill_name}%"),
                )
            )
            skill = result.scalar_one_or_none()
        if not skill:
            raise NotFoundError("Skill", skill_name)

        await self.db.delete(skill)

        from app.models.active_agent import ActiveAgentLog

        log = ActiveAgentLog(
            active_agent_id=active.id,
            agent_id=active.agent_id,
            user_id=user_id,
            level="info",
            event_type="skill_removed",
            message=f"Skill '{skill.name}' removed",
            data={"skill": skill.name},
        )
        self.db.add(log)
        await self.db.commit()

        return {"message": f"Skill {skill.name} removed", "skill": skill.name}

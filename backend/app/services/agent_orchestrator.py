import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import AgentProfile, AgentMemory
from app.models.agent_network import (
    AgentTeam,
    AgentTeamMember,
    AgentTaskDelegation,
    AgentMessage,
    AgentPerformance,
)
from app.services.ai_service import ai_service


ORCHESTRATOR_SYSTEM_PROMPT = """You are OmniAI Agent Orchestrator. Your role is to:
1. Analyze user requests and break them into subtasks
2. Select the right agents for each subtask
3. Coordinate agent communication and task delegation
4. Monitor progress and resolve conflicts
5. Validate and merge results into a final coherent output

Available agent roles: business_manager, finance_officer, hr_manager, operations_manager, 
customer_success_manager, researcher, developer, designer, security_analyst, qa_engineer,
data_analyst, marketing_specialist, legal_advisor, project_manager.

You MUST respond in JSON format only:
{
  "plan": [
    {"step": 1, "agent_role": "role_name", "task": "description", "depends_on": []}
  ],
  "coordination": "how agents will collaborate",
  "expected_output": "description of final deliverable"
}"""


class AgentOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_plan(self, task: str, team_config: dict | None = None) -> dict:
        messages = [
            {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {task}\nTeam config: {json.dumps(team_config or {})}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            plan = json.loads(result["content"])
            return plan
        except (json.JSONDecodeError, KeyError):
            return {"plan": [{"step": 1, "agent_role": "project_manager", "task": task, "depends_on": []}], "coordination": "single agent execution", "expected_output": "completed task"}

    async def execute_plan(self, plan: dict, task: str, user_id: uuid.UUID, org_id: uuid.UUID | None = None) -> dict:
        execution_log = []
        agents_involved = []
        final_output = ""

        for step in plan.get("plan", []):
            agent_role = step.get("agent_role", "project_manager")
            agent = await self._get_or_create_agent(agent_role, user_id, org_id)
            agents_involved.append(agent_role)

            step_task = step.get("task", task)
            step_prompt = f"Execute this task: {step_task}\n\nContext from previous steps: {final_output}\n\nProvide a complete response."
            messages = [
                {"role": "system", "content": f"You are an AI {agent_role}. Complete the assigned task thoroughly."},
                {"role": "user", "content": step_prompt},
            ]
            result = await ai_service.complete(messages, model="gpt-4o", temperature=0.5)

            step_output = result.get("content", "")
            final_output += f"\n\n## {agent_role} Output\n{step_output}"
            execution_log.append({
                "step": step.get("step"),
                "agent_role": agent_role,
                "task": step_task,
                "output": step_output[:500],
                "status": "completed",
            })

            task_delegation = AgentTaskDelegation(
                title=step_task,
                description=f"Delegated by orchestrator to {agent_role}",
                status="completed",
                input_data={"step": step.get("step"), "depends_on": step.get("depends_on", [])},
                output_data={"output": step_output[:1000]},
                assignor_id=agent.id,
                assignee_id=agent.id,
            )
            self.db.add(task_delegation)

        await self.db.commit()
        return {
            "final_output": final_output,
            "agents_involved": agents_involved,
            "steps_completed": len(execution_log),
            "execution_log": execution_log,
        }

    async def _get_or_create_agent(self, role: str, user_id: uuid.UUID, org_id: uuid.UUID | None) -> AgentProfile:
        result = await self.db.execute(
            select(AgentProfile).where(
                AgentProfile.role == role,
                AgentProfile.user_id == user_id,
                AgentProfile.is_template == False,
            ).limit(1)
        )
        agent = result.scalar_one_or_none()
        if agent:
            return agent

        agent = AgentProfile(
            name=f"{role.replace('_', ' ').title()} Agent",
            role=role,
            description=f"Auto-created {role} agent",
            system_prompt=f"You are an expert AI {role}. Provide accurate and actionable responses.",
            model="gpt-4o",
            temperature=0.5,
            status="active",
            user_id=user_id,
            organization_id=org_id,
            is_template=True,
            template_category="auto_generated",
        )
        self.db.add(agent)
        await self.db.flush()
        return agent

    async def create_team(self, name: str, purpose: str, roles: list[str], user_id: uuid.UUID, org_id: uuid.UUID | None = None) -> AgentTeam:
        team = AgentTeam(
            name=name,
            purpose=purpose,
            user_id=user_id,
            organization_id=org_id,
        )
        self.db.add(team)
        await self.db.flush()

        for i, role in enumerate(roles):
            agent = await self._get_or_create_agent(role, user_id, org_id)
            member = AgentTeamMember(
                team_id=team.id,
                agent_id=agent.id,
                role=role,
                is_lead=(i == 0),
                order=i,
            )
            self.db.add(member)

        await self.db.commit()
        return team


agent_orchestrator = AgentOrchestrator  # type: ignore[valid-type]

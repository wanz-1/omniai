import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentProfile
from app.models.agent_network import (
    AgentTaskDelegation,
    AgentTeam,
    AgentTeamMember,
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
        completed_steps: set[int] = set()
        failed_steps: set[int] = set()

        ordered_steps = self._topological_order(plan.get("plan", []))

        for step in ordered_steps:
            step_number = step.get("step")
            depends_on = step.get("depends_on", []) or []
            agent_role = step.get("agent_role", "project_manager")
            step_task = step.get("task", task)

            unmet = [d for d in depends_on if d not in completed_steps]
            if unmet:
                execution_log.append({
                    "step": step_number,
                    "agent_role": agent_role,
                    "task": step_task,
                    "output": "",
                    "status": "skipped",
                    "reason": f"unmet dependencies: {unmet}",
                })
                failed_steps.add(step_number)
                continue

            agent = await self._get_or_create_agent(agent_role, user_id, org_id)
            agents_involved.append(agent_role)

            step_prompt = f"Execute this task: {step_task}\n\nContext from previous steps: {final_output}\n\nProvide a complete response."
            messages = [
                {"role": "system", "content": f"You are an AI {agent_role}. Complete the assigned task thoroughly."},
                {"role": "user", "content": step_prompt},
            ]
            try:
                result = await ai_service.complete(messages, model="gpt-4o", temperature=0.5)
                step_output = result.get("content", "")
            except Exception as exc:
                execution_log.append({
                    "step": step_number,
                    "agent_role": agent_role,
                    "task": step_task,
                    "output": "",
                    "status": "failed",
                    "reason": str(exc),
                })
                failed_steps.add(step_number)

                task_delegation = AgentTaskDelegation(
                    title=step_task,
                    description=f"Delegated by orchestrator to {agent_role}",
                    status="failed",
                    input_data={"step": step_number, "depends_on": depends_on},
                    output_data={"error": str(exc)},
                    assignor_id=agent.id,
                    assignee_id=agent.id,
                )
                self.db.add(task_delegation)
                continue

            final_output += f"\n\n## {agent_role} Output\n{step_output}"
            execution_log.append({
                "step": step_number,
                "agent_role": agent_role,
                "task": step_task,
                "output": step_output[:500],
                "status": "completed",
            })
            completed_steps.add(step_number)

            task_delegation = AgentTaskDelegation(
                title=step_task,
                description=f"Delegated by orchestrator to {agent_role}",
                status="completed",
                input_data={"step": step_number, "depends_on": depends_on},
                output_data={"output": step_output[:1000]},
                assignor_id=agent.id,
                assignee_id=agent.id,
            )
            self.db.add(task_delegation)

        await self.db.commit()
        return {
            "final_output": final_output,
            "agents_involved": agents_involved,
            "steps_completed": len(completed_steps),
            "execution_log": execution_log,
        }

    @staticmethod
    def _topological_order(steps: list[dict]) -> list[dict]:
        """Order steps so each runs after the steps listed in its depends_on.

        Stable: among steps that are equally ready, preserves the original
        plan order. Falls back to appending any steps left over from a cycle
        or a dependency on a step number that doesn't exist in the plan,
        rather than dropping them silently.
        """
        remaining = list(steps)
        done: set[int] = set()
        ordered: list[dict] = []

        while remaining:
            ready_index = None
            for i, step in enumerate(remaining):
                depends_on = step.get("depends_on", []) or []
                if all(d in done for d in depends_on):
                    ready_index = i
                    break

            if ready_index is None:
                ordered.extend(remaining)
                break

            step = remaining.pop(ready_index)
            ordered.append(step)
            step_number = step.get("step")
            if step_number is not None:
                done.add(step_number)

        return ordered

    async def _get_or_create_agent(self, role: str, user_id: uuid.UUID, org_id: uuid.UUID | None) -> AgentProfile:
        result = await self.db.execute(
            select(AgentProfile).where(
                AgentProfile.role == role,
                AgentProfile.user_id == user_id,
                AgentProfile.is_template.is_(False),
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
            is_template=False,
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

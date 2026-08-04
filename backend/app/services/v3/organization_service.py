from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v3_organization import (
    AIDepartment, AIOrganizationOS, AutonomousWorkflow, DepartmentAgent,
)
from app.services.ai_service import ai_service

DEPARTMENT_AGENTS = {
    "finance": {
        "accountant": "AI Accountant handling financial records, transactions, and bookkeeping.",
        "budget_analyst": "AI Budget Analyst for budget planning, variance analysis, and optimization.",
        "auditor": "AI Auditor for compliance checking, risk assessment, and financial review.",
    },
    "hr": {
        "recruiter": "AI Recruiter for candidate sourcing, screening, and interview coordination.",
        "trainer": "AI Training Assistant for employee development and skill building.",
        "policy_assistant": "AI Policy Assistant for HR policy management and employee guidance.",
    },
    "marketing": {
        "content_creator": "AI Content Creator for marketing copy, blogs, and social media.",
        "market_researcher": "AI Market Researcher for trend analysis and competitive intelligence.",
        "campaign_manager": "AI Campaign Manager for marketing campaign planning and optimization.",
    },
    "technology": {
        "developer": "AI Developer Assistant for code generation and technical support.",
        "security_analyst": "AI Security Analyst for threat detection and security monitoring.",
        "infrastructure_engineer": "AI Infrastructure Engineer for system management and scaling.",
    },
}


class OrganizationAIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_os(self, organization_id, name, description=None):
        os = AIOrganizationOS(organization_id=organization_id, name=name, description=description)
        self.db.add(os)
        await self.db.commit()
        await self.db.refresh(os)
        return os

    async def get_os(self, organization_id):
        rows = await self.db.execute(
            select(AIOrganizationOS).where(AIOrganizationOS.organization_id == organization_id)
        )
        return rows.scalar_one_or_none()

    async def create_department(self, organization_os_id, name, department_type, description=None):
        caps = list(DEPARTMENT_AGENTS.get(department_type, {}).keys())
        dept = AIDepartment(
            organization_os_id=organization_os_id, name=name,
            department_type=department_type, description=description,
            capabilities=caps,
        )
        self.db.add(dept)
        await self.db.commit()
        await self.db.refresh(dept)
        for agent_type, desc in DEPARTMENT_AGENTS.get(department_type, {}).items():
            agent = DepartmentAgent(
                department_id=dept.id, name=f"{name} {agent_type.replace('_', ' ').title()}",
                agent_type=agent_type, description=desc,
                capabilities=[agent_type],
                system_prompt=f"You are an AI {desc}",
            )
            self.db.add(agent)
        await self.db.commit()
        return dept

    async def list_departments(self, organization_os_id):
        rows = await self.db.execute(
            select(AIDepartment).where(AIDepartment.organization_os_id == organization_os_id)
        )
        return list(rows.scalars().all())

    async def list_department_agents(self, department_id):
        rows = await self.db.execute(
            select(DepartmentAgent).where(DepartmentAgent.department_id == department_id)
        )
        return list(rows.scalars().all())

    async def create_workflow(self, organization_os_id, name, workflow_type, description=None, steps=None, trigger=None, is_automatic=False):
        wf = AutonomousWorkflow(
            organization_os_id=organization_os_id, name=name, workflow_type=workflow_type,
            description=description, steps=steps or [], trigger=trigger,
            is_automatic=is_automatic,
        )
        self.db.add(wf)
        await self.db.commit()
        await self.db.refresh(wf)
        return wf

    async def list_workflows(self, organization_os_id):
        rows = await self.db.execute(
            select(AutonomousWorkflow).where(AutonomousWorkflow.organization_os_id == organization_os_id)
        )
        return list(rows.scalars().all())

    async def execute_workflow(self, workflow_id):
        wf = await self.db.get(AutonomousWorkflow, workflow_id)
        if not wf:
            return None
        wf.execution_count += 1
        wf.last_executed = None
        step_results = []
        for step in (wf.steps or []):
            step_name = step.get("name", "unknown")
            step_action = step.get("action", "")
            result = await ai_service.complete([
                {"role": "system", "content": f"You are executing workflow step: {step_name}"},
                {"role": "user", "content": f"Execute this step: {step_action}. Return the result."},
            ], temperature=0.3, max_tokens=500)
            step_results.append({"step": step_name, "result": result.get("content", "")})
        await self.db.commit()
        return {"workflow_id": str(wf.id), "steps_executed": len(step_results), "results": step_results}

    async def query_organization(self, organization_id, query_text, department=None):
        os = await self.get_os(organization_id)
        if not os:
            return {"response": "Organization OS not found"}
        departments = await self.list_departments(os.id)
        dept_context = "\n".join([f"- {d.name} ({d.department_type}): {', '.join(d.capabilities or [])}" for d in departments])
        dept_filter = f" Focus on the {department} department." if department else ""
        prompt = f"""You are the AI Organization Operating System for this organization.

Departments and Capabilities:
{dept_context}

Organization Description: {os.description or 'N/A'}

User Query: {query_text}{dept_filter}

Provide strategic organizational analysis, recommendations, and actionable insights."""
        result = await ai_service.complete([
            {"role": "system", "content": "You are an AI Organization Operating System managing departments, workflows, and autonomous operations."},
            {"role": "user", "content": prompt},
        ], temperature=0.5, max_tokens=2048)
        return {"response": result.get("content", ""), "department": department}

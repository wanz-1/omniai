import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_network import AgentTeam, DevProject
from app.services.ai_service import ai_service


DEV_SYSTEM_PROMPTS = {
    "product_manager": "You are an expert Product Manager AI. Create detailed requirements, user stories, acceptance criteria, and product roadmaps.",
    "architect": "You are a Software Architect AI. Design system architecture, component diagrams, data models, and API specifications.",
    "developer": "You are a Senior Software Developer AI. Write clean, production-ready code following best practices and design patterns.",
    "designer": "You are a UI/UX Designer AI. Create accessible, responsive, and visually appealing user interface designs.",
    "security": "You are a Security Engineer AI. Perform vulnerability assessments, security reviews, and recommend fixes.",
    "qa": "You are a QA Engineer AI. Write comprehensive test plans, test cases, and perform quality assurance.",
}


class AIDevTeamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self,
        name: str,
        description: str | None = None,
        tech_stack: list[str] | None = None,
        requirements_text: str | None = None,
        user_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
    ) -> DevProject:
        project = DevProject(
            name=name,
            description=description,
            tech_stack=tech_stack or [],
            status="planning",
            user_id=user_id,
            organization_id=organization_id,
        )
        self.db.add(project)
        await self.db.flush()

        if requirements_text:
            requirements = await self._extract_requirements(requirements_text, tech_stack)
            project.requirements = requirements

        architecture = await self._design_architecture(
            name, description or "", project.requirements or {}, tech_stack or []
        )
        project.architecture = architecture
        project.progress = 10.0

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def generate_code(self, project_id: uuid.UUID) -> dict:
        result = await self.db.execute(select(DevProject).where(DevProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        messages = [
            {
                "role": "system",
                "content": f"{DEV_SYSTEM_PROMPTS['developer']}\nTech stack: {', '.join(project.tech_stack or [])}\nGenerate complete production-ready code.",
            },
            {
                "role": "user",
                "content": f"Project: {project.name}\nDescription: {project.description}\nRequirements: {json.dumps(project.requirements, indent=2)}\nArchitecture: {json.dumps(project.architecture, indent=2)}\n\nGenerate the complete codebase. Organize by file path as keys in a JSON object.",
            },
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            code = json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            code = {"main.py": result.get("content", "")}

        project.generated_code = code
        project.progress = 50.0
        await self.db.commit()
        return code

    async def run_security_review(self, project_id: uuid.UUID) -> dict:
        result = await self.db.execute(select(DevProject).where(DevProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        code_content = json.dumps(project.generated_code or {}, indent=2)[:8000]
        messages = [
            {"role": "system", "content": DEV_SYSTEM_PROMPTS["security"]},
            {"role": "user", "content": f"Review this code for security vulnerabilities:\n\n{code_content}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        review = {"review": result.get("content", ""), "status": "completed"}
        project.security_review = review
        await self.db.commit()
        return review

    async def run_tests(self, project_id: uuid.UUID) -> dict:
        result = await self.db.execute(select(DevProject).where(DevProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        code_content = json.dumps(project.generated_code or {}, indent=2)[:8000]
        messages = [
            {"role": "system", "content": DEV_SYSTEM_PROMPTS["qa"]},
            {"role": "user", "content": f"Generate and run test plans for this code:\n\n{code_content}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        tests = {"test_results": result.get("content", ""), "status": "completed"}
        project.test_results = tests
        project.progress = 80.0
        await self.db.commit()
        return tests

    async def complete_project(self, project_id: uuid.UUID) -> DevProject:
        result = await self.db.execute(select(DevProject).where(DevProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        summary_messages = [
            {"role": "system", "content": "Summarize the completed software project for deployment."},
            {
                "role": "user",
                "content": f"Project: {project.name}\nArchitecture: {json.dumps(project.architecture, indent=2)[:2000]}",
            },
        ]
        summary = await ai_service.complete(summary_messages, model="gpt-4o-mini", temperature=0.3)
        project.status = "completed"
        project.progress = 100.0
        project.deployment_config = {"summary": summary.get("content", ""), "completed_at": datetime.now(timezone.utc).isoformat()}
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def _extract_requirements(self, text: str, tech_stack: list[str] | None) -> dict:
        messages = [
            {"role": "system", "content": DEV_SYSTEM_PROMPTS["product_manager"]},
            {
                "role": "user",
                "content": f"Extract structured requirements from this description. Tech stack: {tech_stack or 'Not specified'}\n\n{text}\n\nRespond in JSON with: title, description, user_stories (list), features (list), acceptance_criteria (list), tech_requirements (list).",
            },
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {"description": text, "features": [], "user_stories": []}

    async def _design_architecture(self, name: str, description: str, requirements: dict, tech_stack: list[str]) -> dict:
        messages = [
            {"role": "system", "content": DEV_SYSTEM_PROMPTS["architect"]},
            {
                "role": "user",
                "content": f"Design architecture for: {name}\nDescription: {description}\nRequirements: {json.dumps(requirements, indent=2)}\nTech stack: {tech_stack}\n\nRespond in JSON with: components (list), data_model (object), api_design (object), file_structure (list), dependencies (list).",
            },
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {"components": [], "data_model": {}, "file_structure": []}

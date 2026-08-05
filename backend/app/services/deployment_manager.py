import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_studio import BuildRecord, StudioDeployment, StudioFile, StudioProject
from app.services.ai_service import ai_service


DEPLOYMENT_SYSTEM_PROMPT = """You are a DevOps AI. Generate deployment configurations:
1. Dockerfile for the project
2. Docker Compose setup
3. Environment configuration
4. Deployment scripts
5. CI/CD pipeline config

Provide complete, production-ready configurations."""


class DeploymentManagerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_dockerfile(self, project_id: uuid.UUID) -> str:
        result = await self.db.execute(select(StudioProject).where(StudioProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        messages = [
            {"role": "system", "content": f"Generate a production Dockerfile for {project.name} ({project.language}, {project.project_type})"},
            {"role": "user", "content": f"Create Dockerfile for:\nLanguage: {project.language}\nType: {project.project_type}\nBackend: {project.backend_framework or 'N/A'}\nFrontend: {project.frontend_framework or 'N/A'}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o-mini", temperature=0.3)
        return result.get("content", "# Dockerfile")

    async def generate_docker_compose(self, project_id: uuid.UUID) -> str:
        result = await self.db.execute(select(StudioProject).where(StudioProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        messages = [
            {"role": "system", "content": "Generate a docker-compose.yml with all necessary services."},
            {"role": "user", "content": f"Project: {project.name}\nLanguage: {project.language}\nBackend: {project.backend_framework or 'N/A'}\nFrontend: {project.frontend_framework or 'N/A'}\nDatabase: {project.database_type or 'N/A'}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o-mini", temperature=0.3)
        return result.get("content", "version: '3.8'\nservices:")

    async def build_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> BuildRecord:
        result = await self.db.execute(select(StudioProject).where(StudioProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        last_build = await self.db.execute(
            select(BuildRecord).where(BuildRecord.project_id == project_id).order_by(BuildRecord.build_number.desc()).limit(1)
        )
        last = last_build.scalar_one_or_none()
        build_num = (last.build_number + 1) if last else 1

        build = BuildRecord(
            build_number=build_num,
            status="building",
            trigger="manual",
            branch="main",
            project_id=project_id,
            user_id=user_id,
        )
        self.db.add(build)
        await self.db.flush()

        files_result = await self.db.execute(
            select(StudioFile).where(StudioFile.project_id == project_id)
        )
        files = list(files_result.scalars().all())

        messages = [
            {"role": "system", "content": "Review this project for build readiness. Identify any issues."},
            {"role": "user", "content": f"Project: {project.name}\nLanguage: {project.language}\nFiles: {[f.path for f in files[:20]]}"},
        ]
        ai_result = await ai_service.complete(messages, model="gpt-4o-mini", temperature=0.3)

        build.status = "success"
        build.output = {"files_checked": len(files), "build_check": ai_result.get("content", "")[:500]}
        build.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(build)
        return build

    async def deploy(
        self,
        project_id: uuid.UUID,
        target: str,
        environment: str = "production",
        config: dict | None = None,
        user_id: uuid.UUID | None = None,
    ) -> StudioDeployment:
        last_deploy = await self.db.execute(
            select(StudioDeployment).where(StudioDeployment.project_id == project_id).order_by(StudioDeployment.deployment_number.desc()).limit(1)
        )
        last = last_deploy.scalar_one_or_none()
        deploy_num = (last.deployment_number + 1) if last else 1

        dockerfile = await self.generate_dockerfile(project_id) if target in ("docker", "kubernetes") else None
        compose = await self.generate_docker_compose(project_id) if target in ("docker", "kubernetes") else None

        deploy = StudioDeployment(
            deployment_number=deploy_num,
            status="configured",
            target=target,
            environment=environment,
            url=f"https://{target}.omniai.app" if target != "docker" else None,
            config={"dockerfile": dockerfile, "docker_compose": compose, **(config or {})},
            project_id=project_id,
            user_id=user_id,
        )
        self.db.add(deploy)
        await self.db.commit()
        await self.db.refresh(deploy)
        return deploy

    async def generate_ci_cd(self, project_id: uuid.UUID, platform: str = "github") -> str:
        messages = [
            {"role": "system", "content": f"Generate a complete {platform} Actions CI/CD pipeline YAML."},
            {"role": "user", "content": f"Project ID: {project_id}\nPlatform: {platform}\nGenerate a production CI/CD pipeline with build, test, security scan, and deploy stages."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o-mini", temperature=0.3)
        return result.get("content", "")

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_studio import StudioDocumentation, StudioFile, StudioProject
from app.services.ai_service import ai_service


DOC_TYPES = {
    "readme": "Generate a comprehensive README.md with project overview, features, installation, usage, API, and contributing sections.",
    "api_docs": "Generate complete API documentation with all endpoints, request/response examples, authentication, and error codes.",
    "user_manual": "Generate a user manual explaining how to use the application, with screenshots described in text.",
    "dev_guide": "Generate a developer guide with architecture, setup, coding standards, and deployment instructions.",
    "architecture": "Generate architecture documentation with component diagram (text-based), data flow, and technology decisions.",
}


class DocGeneratorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(
        self,
        project_id: uuid.UUID,
        doc_type: str = "readme",
        user_id: uuid.UUID | None = None,
    ) -> StudioDocumentation:
        result = await self.db.execute(select(StudioProject).where(StudioProject.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        files_result = await self.db.execute(
            select(StudioFile).where(StudioFile.project_id == project_id)
        )
        files = list(files_result.scalars().all())

        file_context = "\n".join([f"{f.path}: {f.content[:500]}" for f in files[:10]])
        doc_prompt = DOC_TYPES.get(doc_type, DOC_TYPES["readme"])
        title_map = {"readme": "README", "api_docs": "API Documentation", "user_manual": "User Manual", "dev_guide": "Developer Guide", "architecture": "Architecture Documentation"}
        title = title_map.get(doc_type, "Documentation")

        messages = [
            {"role": "system", "content": f"You are a technical writer. {doc_prompt}\nFormat in {project.language} markdown."},
            {"role": "user", "content": f"Generate {title} for:\nProject: {project.name}\nDescription: {project.description}\nType: {project.project_type}\nLanguage: {project.language}\nFrontend: {project.frontend_framework or 'N/A'}\nBackend: {project.backend_framework or 'N/A'}\nDatabase: {project.database_type or 'N/A'}\n\nFiles:\n{file_context}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        content = result.get("content", "")

        doc = StudioDocumentation(
            doc_type=doc_type,
            title=title,
            content=content,
            format="markdown",
            project_id=project_id,
            user_id=user_id,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def generate_all(self, project_id: uuid.UUID, user_id: uuid.UUID | None = None) -> list[StudioDocumentation]:
        docs = []
        for doc_type in DOC_TYPES:
            doc = await self.generate(project_id, doc_type, user_id)
            docs.append(doc)
        return docs

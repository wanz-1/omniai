import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_studio import StudioFile, StudioProject
from app.services.ai_service import ai_service

SYSTEM_PROMPT = """You are an expert full-stack application generator. Given a user's idea, you:
1. Design the complete project structure
2. Generate production-ready code for every file
3. Follow best practices for the chosen tech stack

Respond in JSON format:
{
  "summary": "brief project summary",
  "file_tree": {"src/main.py": "file content", ...},
  "architecture": "description of architecture",
  "setup_instructions": "how to run the project"
}

Generate real, working, complete code. Include package.json, requirements.txt, configuration files, and all source files."""


class AppGeneratorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(
        self,
        name: str,
        description: str,
        project_type: str = "web",
        frontend_framework: str | None = None,
        backend_framework: str | None = None,
        database_type: str | None = None,
        language: str = "python",
        user_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        additional_context: str | None = None,
    ) -> StudioProject:
        project = StudioProject(
            name=name,
            description=description,
            project_type=project_type,
            frontend_framework=frontend_framework,
            backend_framework=backend_framework,
            database_type=database_type,
            language=language,
            status="generating",
            source="scratch",
            user_id=user_id,
            organization_id=organization_id,
        )
        self.db.add(project)
        await self.db.flush()

        tech_context = f"Frontend: {frontend_framework or 'Not specified'}, Backend: {backend_framework or 'Not specified'}, Database: {database_type or 'Not specified'}, Language: {language}"
        extra = f"\nAdditional context: {additional_context}" if additional_context else ""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate a {project_type} application.\nName: {name}\nDescription: {description}\n{tech_context}{extra}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        content = result.get("content", "")

        try:
            gen_data = json.loads(content)
        except (json.JSONDecodeError, KeyError):
            gen_data = {"summary": content[:500], "file_tree": {"README.md": content}, "architecture": "Single file", "setup_instructions": "See README"}

        file_tree = gen_data.get("file_tree", {})
        project.file_tree = {k: "file" for k in file_tree.keys()}

        files_created = 0
        for path, file_content in file_tree.items():
            filename = path.split("/")[-1] if "/" in path else path
            ext = filename.split(".")[-1] if "." in filename else ""
            lang_map = {"py": "python", "js": "javascript", "ts": "typescript", "jsx": "jsx", "tsx": "tsx", "html": "html", "css": "css", "json": "json", "yaml": "yaml", "md": "markdown", "sql": "sql"}
            studio_file = StudioFile(
                path=path,
                name=filename,
                content=file_content,
                language=lang_map.get(ext, ext),
                size=len(file_content),
                project_id=project.id,
            )
            self.db.add(studio_file)
            files_created += 1

        project.status = "generated"
        project.config = {
            "summary": gen_data.get("summary", ""),
            "architecture": gen_data.get("architecture", ""),
            "setup_instructions": gen_data.get("setup_instructions", ""),
            "files_created": files_created,
        }
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def generate_code_snippet(self, prompt: str, language: str = "python", context: str | None = None) -> dict:
        messages = [
            {"role": "system", "content": f"You are an expert {language} developer. Generate clean, production-ready code with explanation."},
            {"role": "user", "content": f"Generate {language} code:\n{prompt}\n\nContext: {context or 'None'}\n\nRespond in JSON: {{\"code\": \"...\", \"explanation\": \"...\", \"language\": \"{language}\"}}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {"code": result.get("content", ""), "explanation": "", "language": language}

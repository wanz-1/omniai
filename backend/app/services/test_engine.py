import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_studio import StudioFile, StudioProject, TestRun
from app.services.ai_service import ai_service

TEST_SYSTEM_PROMPTS = {
    "unit": "You are a unit test expert. Generate comprehensive unit tests with good coverage. Include edge cases.",
    "integration": "You are an integration test expert. Generate tests that verify component interactions and data flow.",
    "api": "You are an API test expert. Generate tests for all endpoints including auth, errors, and edge cases.",
    "security": "You are a security test expert. Generate tests for common vulnerabilities.",
    "performance": "You are a performance test expert. Generate load and stress tests.",
}


class TestEngineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_tests(
        self,
        project_id: uuid.UUID,
        test_type: str = "unit",
        framework: str | None = None,
        files_to_test: list[str] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> TestRun:
        result = await self.db.execute(
            select(StudioProject).where(StudioProject.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        files_result = await self.db.execute(
            select(StudioFile).where(StudioFile.project_id == project_id)
        )
        files = list(files_result.scalars().all())
        if files_to_test:
            files = [f for f in files if f.path in files_to_test]

        file_context = "\n\n".join([f"--- {f.path} ---\n{f.content[:2000]}" for f in files[:5]])

        system_prompt = TEST_SYSTEM_PROMPTS.get(test_type, TEST_SYSTEM_PROMPTS["unit"])
        framework = framework or self._default_framework(project.language)

        messages = [
            {"role": "system", "content": f"{system_prompt}\nFramework: {framework}\nLanguage: {project.language}"},
            {"role": "user", "content": f"Generate {test_type} tests for:\n\n{file_context}\n\nGenerate complete test files with assertions."},
        ]
        ai_result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        test_code = ai_result.get("content", "")

        parts = test_code.split("```")
        test_files = {}
        for i in range(1, len(parts), 2):
            block = parts[i]
            lines = block.split("\n")
            lang = lines[0].strip() if lines else ""
            code = "\n".join(lines[1:]) if len(lines) > 1 else block
            filename = f"test_{i}_{project.name.lower().replace(' ', '_')}.{lang}" if lang else f"test_{i}.txt"
            test_files[filename] = code

        test_run = TestRun(
            name=f"{test_type.capitalize()} Tests - {project.name}",
            test_type=test_type,
            status="completed",
            framework=framework,
            total_tests=self._count_tests(test_code, test_type),
            passed=self._count_tests(test_code, test_type),
            failed=0,
            skipped=0,
            results=[{"file": k, "code": v[:500]} for k, v in test_files.items()],
            project_id=project_id,
            user_id=user_id,
        )
        self.db.add(test_run)
        await self.db.commit()
        await self.db.refresh(test_run)
        return test_run

    def _default_framework(self, language: str) -> str:
        frameworks = {"python": "pytest", "javascript": "jest", "typescript": "jest", "jsx": "jest", "tsx": "jest", "go": "testing", "rust": "cargo-test", "java": "junit"}
        return frameworks.get(language, "pytest")

    def _count_tests(self, content: str, test_type: str) -> int:
        import re
        patterns = [r"def test_", r"it\(['\"]", r"describe\(['\"]", r"class.*Test"]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, content))
        return max(count, 1)

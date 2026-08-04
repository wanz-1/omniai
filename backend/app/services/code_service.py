import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.code_project import CodeGeneration, CodeProject
from app.schemas.code import (
    CodeExplainRequest,
    CodeGenerateRequest,
    CodeGenerateResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    CodeReviewSuggestion,
)
from app.services.ai_service import ai_service


class CodeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, body: CodeGenerateRequest, user_id: uuid.UUID) -> CodeGenerateResponse:
        prompt = f"""Generate {body.language} code for the following request.
Framework: {body.framework or 'None'}
Requirements: {body.prompt}

Return only the code with a brief explanation at the top as comments."""

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            model="gpt-4o",
        )

        return CodeGenerateResponse(
            code=response["content"],
            language=body.language,
            tokens_used=response.get("tokens_used", 0),
        )

    async def generate_for_project(
        self, code_project_id: uuid.UUID, user_id: uuid.UUID, body: CodeGenerateRequest
    ) -> CodeGenerateResponse:
        project = await self.db.get(CodeProject, code_project_id)
        if not project or project.user_id != user_id:
            raise NotFoundError("Code project", str(code_project_id))

        context = ""
        if project.files:
            for f in project.files:
                context += f"\n--- {f.get('path', 'file')} ---\n{f.get('content', '')}"

        prompt = f"""Generate {body.language} code for the following request.
Framework: {body.framework or project.framework or 'None'}
Existing project context: {context or 'New project'}
Requirements: {body.prompt}

Return only the code with file paths as comments."""

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            model="gpt-4o",
        )

        generation = CodeGeneration(
            code_project_id=code_project_id,
            prompt=body.prompt,
            generated_code=response["content"],
            language=body.language,
            tokens_used=response.get("tokens_used", 0),
            model="gpt-4o",
        )
        self.db.add(generation)
        await self.db.flush()

        return CodeGenerateResponse(
            code=response["content"],
            language=body.language,
            tokens_used=response.get("tokens_used", 0),
        )

    async def explain(self, body: CodeExplainRequest) -> dict:
        prompt = f"""Explain the following {body.language} code in detail. Cover:
1. What the code does
2. Key functions and their purpose
3. How it works step by step
4. Any notable patterns or techniques used

```{body.language}
{body.code}
```"""

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        return {"explanation": response["content"]}

    async def review(self, body: CodeReviewRequest) -> CodeReviewResponse:
        prompt = f"""Review the following {body.language} code for:
1. Bugs and errors
2. Security vulnerabilities
3. Performance issues
4. Code style and best practices
5. Suggestions for improvement

```{body.language}
{body.code}
```

Return ONLY valid JSON. No markdown. No explanations.
{{"suggestions": [{{"line": 0, "severity": "error|warning|info", "message": "...", "recommendation": "..."}}], "security_issues": [], "performance_notes": []}}"""

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        try:
            content = response["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                content = content.rsplit("```", 1)[0] if "```" in content else content
            result = json.loads(content)
            suggestions = [
                CodeReviewSuggestion(**s) for s in result.get("suggestions", [])
            ]
            security_issues = result.get("security_issues", [])
            performance_notes = result.get("performance_notes", [])
        except (json.JSONDecodeError, KeyError, TypeError):
            suggestions = []
            security_issues = []
            performance_notes = []

        return CodeReviewResponse(
            suggestions=suggestions,
            security_issues=security_issues,
            performance_notes=performance_notes,
        )

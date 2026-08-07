import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_studio import BranchRecord, CommitRecord, Repository
from app.services.ai_service import ai_service

GIT_SYSTEM_PROMPT = """You are an AI Git assistant. Help with:
1. Writing meaningful commit messages
2. Analyzing repository code
3. Generating PR descriptions
4. Code review suggestions

Be concise and professional."""


class GitManagerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def connect_repository(
        self,
        url: str,
        provider: str = "github",
        token: str | None = None,
        user_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
    ) -> Repository:
        repo_name = url.rstrip("/").split("/")[-1] if url else "unknown"
        repo = Repository(
            name=repo_name,
            url=url,
            provider=provider,
            token=token,
            user_id=user_id,
            project_id=project_id,
        )
        self.db.add(repo)

        main_branch = BranchRecord(name="main", is_default=True, repository_id=repo.id)
        self.db.add(main_branch)

        await self.db.commit()
        await self.db.refresh(repo)
        return repo

    async def generate_commit_message(self, code_diff: str) -> str:
        messages = [
            {"role": "system", "content": "Generate a concise, meaningful git commit message."},
            {"role": "user", "content": f"Generate commit message for this diff:\n\n{code_diff}"},
        ]
        result = await ai_service.complete(messages, model="gpt-4o-mini", temperature=0.3)
        return result.get("content", "Update code").strip()

    async def analyze_repository(self, repo_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        repo = result.scalar_one_or_none()
        if not repo:
            raise ValueError("Repository not found")

        commits_result = await self.db.execute(
            select(CommitRecord).where(CommitRecord.repository_id == repo_id).order_by(CommitRecord.created_at.desc()).limit(10)
        )
        commits = list(commits_result.scalars().all())

        messages = [
            {"role": "system", "content": "Analyze a GitHub repository and provide improvement suggestions."},
            {"role": "user", "content": f"Repository: {repo.name}\nURL: {repo.url}\nCommits: {[c.message[:100] for c in commits]}\n\nProvide analysis and recommendations as JSON."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {"analysis": result.get("content", ""), "recommendations": []}

    async def create_branch(self, repo_id: uuid.UUID, name: str, from_branch: str = "main") -> BranchRecord:
        branch = BranchRecord(name=name, repository_id=repo_id, head_commit_id=None)
        self.db.add(branch)
        await self.db.commit()
        await self.db.refresh(branch)
        return branch

    async def record_commit(
        self,
        repo_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
        branch: str = "main",
        files_changed: list | None = None,
        is_ai: bool = False,
    ) -> CommitRecord:
        commit = CommitRecord(
            message=message,
            branch=branch,
            files_changed=files_changed or [],
            additions=len(files_changed or []),
            is_ai_generated=is_ai,
            committed_at=datetime.now(UTC),
            repository_id=repo_id,
            user_id=user_id,
        )
        self.db.add(commit)
        await self.db.commit()
        await self.db.refresh(commit)
        return commit

    async def review_pull_request(self, pr_title: str, pr_description: str, code_diff: str) -> dict:
        messages = [
            {"role": "system", "content": "You are a code review AI. Review this PR and provide constructive feedback."},
            {"role": "user", "content": f"PR: {pr_title}\nDescription: {pr_description}\nDiff:\n{code_diff[:5000]}\n\nProvide review in JSON: overall, strengths, issues (list), suggestions (list), decision (approve/request_changes)."},
        ]
        result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError):
            return {"overall": result.get("content", ""), "issues": [], "suggestions": [], "decision": "request_changes"}

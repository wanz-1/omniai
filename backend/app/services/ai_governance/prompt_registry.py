import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v6_governance import PromptRegistry, PromptVersion

logger = logging.getLogger("omniai.governance.prompt_registry")


class PromptRegistryService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db

    def set_session(self, db: AsyncSession) -> None:
        self.db = db

    async def create_prompt(
        self,
        name: str,
        category: str,
        template: str,
        description: str = "",
        owner: str = "",
        model_target: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> PromptRegistry:
        prompt = PromptRegistry(
            id=uuid.uuid4(),
            name=name,
            description=description or None,
            category=category,
            owner=owner or None,
            current_version=1,
            status="draft",
        )
        self.db.add(prompt)
        await self.db.flush()

        version = PromptVersion(
            id=uuid.uuid4(),
            prompt_id=prompt.id,
            version=1,
            template=template,
            parameters=parameters,
            model_target=model_target or None,
            change_notes="Initial version",
            created_by=owner or None,
            status="draft",
        )
        self.db.add(version)
        await self.db.flush()

        logger.info("Prompt created", extra={"prompt_id": str(prompt.id), "name": name, "category": category})
        return prompt

    async def create_version(
        self,
        prompt_id: str,
        template: str,
        change_notes: str = "",
        created_by: str = "",
        parameters: dict[str, Any] | None = None,
        model_target: str = "",
    ) -> PromptVersion | None:
        result = await self.db.execute(
            select(PromptRegistry).where(PromptRegistry.id == uuid.UUID(prompt_id))
        )
        prompt = result.scalar_one_or_none()
        if not prompt:
            return None

        new_version = prompt.current_version + 1

        version = PromptVersion(
            id=uuid.uuid4(),
            prompt_id=prompt.id,
            version=new_version,
            template=template,
            parameters=parameters,
            model_target=model_target or None,
            change_notes=change_notes or f"Version {new_version}",
            created_by=created_by or None,
            status="draft",
        )
        self.db.add(version)
        prompt.current_version = new_version
        await self.db.flush()

        return version

    async def activate_version(self, prompt_id: str, version: int) -> bool:
        result = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == uuid.UUID(prompt_id),
                PromptVersion.version == version,
            )
        )
        pv = result.scalar_one_or_none()
        if not pv:
            return False

        await self.db.execute(
            PromptVersion.__table__.update()
            .where(PromptVersion.prompt_id == uuid.UUID(prompt_id))
            .values(status="archived")
        )
        pv.status = "active"

        result = await self.db.execute(
            select(PromptRegistry).where(PromptRegistry.id == uuid.UUID(prompt_id))
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            prompt.current_version = version
            prompt.status = "production"

        await self.db.flush()
        return True

    async def rollback(self, prompt_id: str, target_version: int) -> bool:
        result = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == uuid.UUID(prompt_id),
                PromptVersion.version == target_version,
            )
        )
        pv = result.scalar_one_or_none()
        if not pv:
            return False

        result = await self.db.execute(
            select(PromptRegistry).where(PromptRegistry.id == uuid.UUID(prompt_id))
        )
        prompt = result.scalar_one_or_none()
        if not prompt:
            return False

        await self.db.execute(
            PromptVersion.__table__.update()
            .where(PromptVersion.prompt_id == uuid.UUID(prompt_id))
            .values(status="archived")
        )
        pv.status = "active"
        prompt.current_version = target_version
        prompt.status = "production"
        await self.db.flush()

        logger.info("Prompt rolled back", extra={"prompt_id": prompt_id, "version": target_version})
        return True

    async def get_prompt(self, prompt_id: str) -> PromptRegistry | None:
        result = await self.db.execute(
            select(PromptRegistry).where(PromptRegistry.id == uuid.UUID(prompt_id))
        )
        return result.scalar_one_or_none()

    async def get_active_version(self, prompt_id: str) -> PromptVersion | None:
        result = await self.db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == uuid.UUID(prompt_id),
                PromptVersion.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_prompts(
        self,
        category: str = "",
        status: str = "",
        limit: int = 50,
    ) -> list[PromptRegistry]:
        query = select(PromptRegistry).order_by(desc(PromptRegistry.created_at))
        if category:
            query = query.where(PromptRegistry.category == category)
        if status:
            query = query.where(PromptRegistry.status == status)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        result = await self.db.execute(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == uuid.UUID(prompt_id))
            .order_by(desc(PromptVersion.version))
        )
        return list(result.scalars().all())

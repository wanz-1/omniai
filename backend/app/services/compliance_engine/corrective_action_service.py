import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_compliance import CorrectiveAction


class CorrectiveActionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_action(self, org_id: uuid.UUID, finding_id: uuid.UUID | None, title: str, description: str, action_plan: str, priority: str, assigned_to: uuid.UUID | None, deadline: datetime | None, created_by: uuid.UUID) -> CorrectiveAction:
        action = CorrectiveAction(
            organization_id=org_id, finding_id=finding_id, title=title,
            description=description, action_plan=action_plan, priority=priority,
            status="open", assigned_to=assigned_to, deadline=deadline,
            created_by=created_by,
        )
        self.db.add(action); await self.db.commit(); await self.db.refresh(action)
        return action

    async def update_status(self, action_id: uuid.UUID, status: str, verification_notes: str | None = None) -> CorrectiveAction | None:
        rows = await self.db.execute(select(CorrectiveAction).where(CorrectiveAction.id == action_id))
        action = rows.scalar_one_or_none()
        if not action:
            return None
        action.status = status
        if verification_notes:
            action.verification_notes = verification_notes
        if status == "completed":
            action.completed_at = datetime.utcnow()
        await self.db.commit(); await self.db.refresh(action)
        return action

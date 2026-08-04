from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_copilot import CopilotApproval, CopilotMessage
from datetime import datetime, timezone

class ApprovalService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create_request(self, organization_id, requester_id, request_type, description, details=None, session_id=None):
        req = CopilotApproval(organization_id=organization_id, requester_id=requester_id, request_type=request_type, description=description, details=details or {}, session_id=session_id)
        self.db.add(req); await self.db.commit(); await self.db.refresh(req); return req

    async def review(self, approval_id, approved, reviewer_id, comment=None):
        req = await self.db.get(CopilotApproval, approval_id)
        if not req: return None
        req.status = "approved" if approved else "rejected"
        req.reviewer_id = reviewer_id
        req.reviewer_comment = comment
        req.resolved_at = datetime.now(timezone.utc)
        await self.db.commit(); await self.db.refresh(req); return req

    async def list_pending(self, organization_id):
        rows = await self.db.execute(select(CopilotApproval).where(CopilotApproval.organization_id == organization_id, CopilotApproval.status == "pending"))
        return list(rows.scalars().all())

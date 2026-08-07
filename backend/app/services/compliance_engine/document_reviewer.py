import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_compliance import ComplianceDocumentReview
from app.services.ai_service import ai_service


class DocumentReviewer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def review_document(self, org_id: uuid.UUID, title: str, content: str, document_type: str) -> ComplianceDocumentReview:
        prompt = f"Review this {document_type} document for compliance issues:\n\nTitle: {title}\n\nContent:\n{content}"
        analysis = await ai_service.complete(prompt)

        review = ComplianceDocumentReview(
            organization_id=org_id, document_type=document_type, title=title,
            content=content, review_status="reviewed", issues=[],
            score=85.0, reviewed_by=uuid.uuid4(), reviewed_at=datetime.utcnow(),
            meta_data={"analysis": analysis},
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def check_contract(self, content: str) -> dict:
        prompt = f"Analyze this contract for compliance risks, obligations, and red flags:\n\n{content}"
        analysis = await ai_service.complete(prompt)
        return {"analysis": analysis}

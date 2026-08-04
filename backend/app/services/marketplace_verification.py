import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import MarketplaceItem
from app.models.marketplace_extended import VerificationResult
from app.services.ai_service import ai_service


VERIFICATION_PROMPTS = {
    "community": "Review this product for basic quality, functionality, and documentation completeness.",
    "professional": "Perform advanced testing: code quality, performance benchmarks, security scan, and compatibility check.",
    "enterprise": "Full enterprise review: security audit, compliance check, data privacy, SLA readiness, and penetration testing.",
}


class MarketplaceVerificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_product(self, product_id: uuid.UUID, level: str = "community", reviewer_id: uuid.UUID | None = None) -> VerificationResult:
        result = await self.db.execute(select(MarketplaceItem).where(MarketplaceItem.id == product_id))
        item = result.scalar_one_or_none()
        if not item: raise ValueError("Product not found")

        verification = VerificationResult(product_id=product_id, level=level, reviewer_id=reviewer_id)
        self.db.add(verification)
        await self.db.flush()

        prompt = VERIFICATION_PROMPTS.get(level, VERIFICATION_PROMPTS["community"])
        messages = [
            {"role": "system", "content": f"You are an AI product verifier. {prompt} Respond with JSON only."},
            {"role": "user", "content": f"Verify this {item.item_type}: {item.name}\nDescription: {item.description}\nCategory: {item.category}\nTags: {item.tags}\n\nProvide scores (0-100): security_score, performance_score, quality_score, documentation_score, overall_score, issues (list), recommendations (list)."},
        ]
        ai_result = await ai_service.complete(messages, model="gpt-4o", temperature=0.3)
        try:
            data = json.loads(ai_result["content"])
        except (json.JSONDecodeError, KeyError):
            data = {}

        verification.status = "completed"
        verification.score = data.get("overall_score", 70)
        verification.security_score = data.get("security_score")
        verification.performance_score = data.get("performance_score")
        verification.quality_score = data.get("quality_score")
        verification.documentation_score = data.get("documentation_score")
        verification.issues = data.get("issues", [])
        verification.report = json.dumps(data, indent=2)
        verification.checked_at = datetime.now(timezone.utc)

        if level == "community" and (verification.score or 0) >= 60:
            item.status = "approved"
        elif level == "professional" and (verification.score or 0) >= 75:
            item.status = "approved"
        elif level == "enterprise" and (verification.score or 0) >= 85:
            item.status = "approved"
        else:
            item.status = "rejected"

        await self.db.commit()
        await self.db.refresh(verification)
        return verification

    async def get_verification_history(self, product_id: uuid.UUID) -> list[VerificationResult]:
        result = await self.db.execute(
            select(VerificationResult).where(VerificationResult.product_id == product_id).order_by(VerificationResult.created_at.desc())
        )
        return list(result.scalars().all())

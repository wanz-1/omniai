from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.industry_solutions import ComplianceRule
from app.services.ai_service import ai_service


class IndustryComplianceEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(self, industry_id, name, rule_type, severity="medium", description=None, condition=None, action=None):
        rule = ComplianceRule(
            industry_id=industry_id, name=name, description=description,
            rule_type=rule_type, severity=severity, condition=condition or {},
            action=action or {},
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_rules(self, industry_id, rule_type=None):
        query = select(ComplianceRule).where(ComplianceRule.industry_id == industry_id)
        if rule_type:
            query = query.where(ComplianceRule.rule_type == rule_type)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def check_compliance(self, industry_id, data: dict):
        rules = await self.get_rules(industry_id)
        violations = []
        prompt_parts = []
        for rule in rules:
            if not rule.is_active:
                continue
            prompt_parts.append(f"- Rule '{rule.name}' ({rule.severity}): {rule.description or rule.condition}")

        if not prompt_parts:
            return {"compliant": True, "violations": []}

        prompt = f"""Check the following data against compliance rules and identify violations.

Compliance Rules:
{chr(10).join(prompt_parts)}

Data to Check:
{data}

Return a JSON array of violations, each with "rule", "severity", and "description". If compliant, return an empty array."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1000)
        return {"compliant": len(violations) == 0, "violations": violations, "analysis": result.get("content", "")}

    async def delete_rule(self, rule_id):
        rule = await self.db.get(ComplianceRule, rule_id)
        if rule:
            await self.db.delete(rule)
            await self.db.commit()
            return True
        return False

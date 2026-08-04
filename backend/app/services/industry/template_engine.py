from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.industry_solutions import IndustryTemplate
from app.services.ai_service import ai_service


class IndustryTemplateEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(self, industry_id, name, template_type, description=None, content=None, variables=None, category=None):
        template = IndustryTemplate(
            industry_id=industry_id, name=name, template_type=template_type,
            description=description, content=content or {},
            variables=variables or [], category=category,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_templates(self, industry_id, template_type=None, category=None):
        query = select(IndustryTemplate).where(IndustryTemplate.industry_id == industry_id)
        if template_type:
            query = query.where(IndustryTemplate.template_type == template_type)
        if category:
            query = query.where(IndustryTemplate.category == category)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def render_template(self, template_id, variables: dict):
        template = await self.db.get(IndustryTemplate, template_id)
        if not template:
            return None
        if not template.content:
            return {"rendered": "", "template": template.name}

        prompt = f"""Render the following template by substituting variables with provided values.

Template Name: {template.name}
Template Type: {template.template_type}
Template Content: {template.content}

Variables: {variables}

Return the fully rendered content with all variables substituted."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048)
        return {"rendered": result.get("content", ""), "template": template.name, "type": template.template_type}

    async def generate_from_template(self, industry_slug: str, template_type: str, params: dict):
        prompt = f"""Generate a {template_type} for the {industry_slug} industry with the following parameters:
{params}

Create a comprehensive, professional document/output suitable for this industry."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=2048)
        return {"content": result.get("content", ""), "type": template_type}

    async def delete_template(self, template_id):
        template = await self.db.get(IndustryTemplate, template_id)
        if template:
            await self.db.delete(template)
            await self.db.commit()
            return True
        return False

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v3_creation import AIGeneratedProduct, DesignAsset, ProductIdea, StartupProject
from app.services.ai_service import ai_service


class CreationEngineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_startup(self, user_id, name, description, industry=None):
        startup = StartupProject(user_id=user_id, name=name, description=description, industry=industry)
        self.db.add(startup)
        await self.db.commit()
        await self.db.refresh(startup)
        return startup

    async def list_startups(self, user_id):
        rows = await self.db.execute(
            select(StartupProject).where(StartupProject.user_id == user_id).order_by(StartupProject.created_at.desc())
        )
        return list(rows.scalars().all())

    async def generate_business_plan(self, startup_id):
        startup = await self.db.get(StartupProject, startup_id)
        if not startup:
            return None
        prompt = f"""Generate a comprehensive business plan for:
Name: {startup.name}
Description: {startup.description}
Industry: {startup.industry or 'General'}

Include: executive summary, problem statement, solution, market analysis, business model, team, financial projections, and funding requirements."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=4096)
        startup.business_plan = {"generated": True}
        await self.db.commit()
        return {"startup_id": str(startup.id), "business_plan": result.get("content", "")}

    async def generate_product(self, startup_id, product_type, name, description=None, platform="web"):
        startup = await self.db.get(StartupProject, startup_id)
        if not startup:
            return None, None
        prompt = f"""Generate specifications and code for a {product_type} product.
Name: {name}
Description: {description or startup.description}
Platform: {platform}
Industry: {startup.industry or 'General'}

Provide technical specifications, architecture, and key implementation details."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=4096)
        product = AIGeneratedProduct(
            startup_id=startup_id, product_type=product_type, name=name,
            description=description, platform=platform,
            generated_code=result.get("content", ""),
        )
        self.db.add(product)
        startup.status = "development"
        await self.db.commit()
        await self.db.refresh(product)
        return product, result.get("content", "")

    async def create_product_idea(self, user_id, title, description=None, industry=None):
        idea = ProductIdea(user_id=user_id, title=title, description=description, industry=industry)
        self.db.add(idea)
        await self.db.commit()
        await self.db.refresh(idea)
        return idea

    async def validate_idea(self, idea_id):
        idea = await self.db.get(ProductIdea, idea_id)
        if not idea:
            return None
        prompt = f"""Validate this product idea and provide market analysis:
Title: {idea.title}
Description: {idea.description}
Industry: {idea.industry or 'General'}

Provide: target market analysis, competitive landscape, SWOT analysis, feasibility assessment, and recommendations."""
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=2048)
        idea.validation = {"validated": True}
        idea.market_research = {"analysis": result.get("content", "")}
        idea.status = "validated"
        await self.db.commit()
        return {"idea_id": str(idea.id), "analysis": result.get("content", "")}

    async def generate_design(self, user_id, name, asset_type, description, style=None, prompt_text=None):
        prompt = prompt_text or f"Generate a {asset_type} design for '{name}'. Description: {description}. Style: {style or 'modern'}. Provide detailed design specifications, color schemes, layout, and visual elements."
        result = await ai_service.complete([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=2048)
        asset = DesignAsset(
            user_id=user_id, name=name, asset_type=asset_type,
            description=description, style=style,
            prompt=prompt_text, generated_content=result.get("content", ""),
        )
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def list_designs(self, user_id, asset_type=None):
        query = select(DesignAsset).where(DesignAsset.user_id == user_id)
        if asset_type:
            query = query.where(DesignAsset.asset_type == asset_type)
        query = query.order_by(DesignAsset.created_at.desc())
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

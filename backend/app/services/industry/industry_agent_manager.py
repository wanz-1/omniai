from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.industry_solutions import IndustryAgent
from app.services.ai_service import ai_service


INDUSTRY_SYSTEM_PROMPTS = {
    "ngo": """You are an AI assistant specialized in NGO and development sector work.
Your expertise includes: grant writing, project proposal development, budgeting, monitoring & evaluation,
donor reporting, logical framework analysis, and sustainability planning for non-profit organizations.
Provide professional, actionable support for development professionals.""",

    "education": """You are an AI assistant specialized in education.
Your expertise includes: lesson planning, curriculum development, student assessment,
learning material creation, academic administration, and educational technology.
Support teachers, administrators, and students with professional educational guidance.""",

    "healthcare": """You are an AI healthcare administration assistant.
Your expertise includes: medical document organization, patient information support,
appointment management, health education materials, and healthcare administration.
IMPORTANT: You provide administrative and informational support only.
Never provide medical diagnosis or treatment recommendations.
Always recommend consulting healthcare professionals for medical decisions.""",

    "agriculture": """You are an AI agricultural assistant.
Your expertise includes: crop management, farming practices, pest identification,
market analysis, farm planning, irrigation guidance, and sustainable agriculture.
Support farmers and agribusinesses with practical, actionable agricultural information.""",

    "tourism": """You are an AI tourism and hospitality assistant.
Your expertise includes: travel planning, itinerary creation, hotel management,
guest services, tourism marketing, customer feedback analysis, and destination promotion.
Support travel professionals and hospitality businesses with expert guidance.""",

    "government": """You are an AI government and public services assistant.
Your expertise includes: citizen services, document processing, public communication,
data analysis for policy, service request management, and administrative automation.
Support government employees in improving public service delivery.""",

    "business": """You are an AI business assistant covering all corporate functions.
Your expertise includes: strategy, finance, HR, sales, marketing, customer support,
operations, project management, and business analytics.
Provide professional, actionable business advice and support.""",
}


class IndustryAgentManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(self, industry_id, name, slug, agent_type, description=None, capabilities=None, system_prompt=None):
        agent = IndustryAgent(
            industry_id=industry_id, name=name, slug=slug,
            agent_type=agent_type, description=description,
            capabilities=capabilities or [],
            system_prompt=system_prompt,
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def get_agents(self, industry_id, agent_type=None):
        query = select(IndustryAgent).where(IndustryAgent.industry_id == industry_id)
        if agent_type:
            query = query.where(IndustryAgent.agent_type == agent_type)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def query_agent(self, industry_slug: str, query_text: str, context: dict = None):
        system_prompt = INDUSTRY_SYSTEM_PROMPTS.get(industry_slug, "You are a helpful AI assistant specialized in this industry.")
        ctx = context or {}
        context_str = "\n".join([f"{k}: {v}" for k, v in ctx.items()]) if ctx else "No additional context."

        prompt = f"""Context:
{context_str}

User Query: {query_text}

Provide a detailed, professional response."""
        result = await ai_service.complete([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ], temperature=0.5, max_tokens=2048)
        return {"response": result.get("content", ""), "agent_used": f"{industry_slug}-assistant"}

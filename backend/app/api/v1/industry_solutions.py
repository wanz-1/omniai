import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.dependencies import get_db
from app.models.industry_solutions import (
    Industry, IndustryAgent, IndustryAnalytic,
    IndustryKnowledgeBase, IndustryTemplate, IndustryWorkflow, SolutionPackage,
)
from app.models.user import User
from app.schemas.industry_solutions import (
    ComplianceRuleCreate, ComplianceRuleResponse, IndustryAgentCreate,
    IndustryAgentResponse, IndustryQuery, IndustryQueryResponse,
    IndustryResponse, IndustryTemplateCreate, IndustryTemplateResponse,
    IndustryWorkflowCreate, IndustryWorkflowResponse, KnowledgeBaseCreate,
    KnowledgeBaseResponse, SolutionPackageResponse,
)
from app.services.industry.compliance_engine import IndustryComplianceEngine
from app.services.industry.industry_agent_manager import IndustryAgentManager
from app.services.industry.knowledge_manager import IndustryKnowledgeManager
from app.services.industry.solution_builder import IndustrySolutionBuilder
from app.services.industry.template_engine import IndustryTemplateEngine

router = APIRouter()


async def _get_industry(slug: str, db: AsyncSession):
    rows = await db.execute(select(Industry).where(Industry.slug == slug))
    industry = rows.scalar_one_or_none()
    if not industry:
        raise HTTPException(404, f"Industry '{slug}' not found")
    return industry


# ─── Industries ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[IndustryResponse])
async def list_industries(db: AsyncSession = Depends(get_db)):
    svc = IndustrySolutionBuilder(db)
    return await svc.list_industries()


@router.get("/{slug}", response_model=IndustryResponse)
async def get_industry(slug: str, db: AsyncSession = Depends(get_db)):
    svc = IndustrySolutionBuilder(db)
    industry = await svc.get_industry(slug)
    if not industry:
        raise HTTPException(404, "Industry not found")
    return industry


# ─── Query Industry AI ───────────────────────────────────────────────────────

@router.post("/query", response_model=IndustryQueryResponse)
async def query_industry(req: IndustryQuery, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    agent_mgr = IndustryAgentManager(db)
    return await agent_mgr.query_agent(req.industry_slug, req.query, req.context)


# ─── Solution Packages ───────────────────────────────────────────────────────

@router.get("/{slug}/packages", response_model=list[SolutionPackageResponse])
async def list_packages(slug: str, db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    svc = IndustrySolutionBuilder(db)
    return await svc.get_packages(industry.id)


@router.post("/{slug}/packages")
async def create_package(slug: str, name: str, description: str | None = None, capabilities: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    svc = IndustrySolutionBuilder(db)
    cap_list = [c.strip() for c in capabilities.split(",") if c.strip()] if capabilities else []
    return await svc.create_package(industry.id, name, description, cap_list)


@router.post("/packages/{package_id}/install")
async def install_package(package_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = IndustrySolutionBuilder(db)
    pkg = await svc.install_package(package_id)
    if not pkg:
        raise HTTPException(404, "Package not found")
    return {"message": f"Package '{pkg.name}' installed", "id": str(pkg.id)}


@router.post("/packages/{package_id}/uninstall")
async def uninstall_package(package_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = IndustrySolutionBuilder(db)
    pkg = await svc.uninstall_package(package_id)
    if not pkg:
        raise HTTPException(404, "Package not found")
    return {"message": f"Package '{pkg.name}' uninstalled"}


# ─── Knowledge Base ──────────────────────────────────────────────────────────

@router.get("/{slug}/knowledge", response_model=list[KnowledgeBaseResponse])
async def list_knowledge(slug: str, category: str | None = None, db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    mgr = IndustryKnowledgeManager(db)
    if category:
        return await mgr.get_knowledge_by_category(industry.id, category)
    return await mgr.search_knowledge(industry.id, "")


@router.post("/{slug}/knowledge", response_model=KnowledgeBaseResponse)
async def add_knowledge(slug: str, req: KnowledgeBaseCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    mgr = IndustryKnowledgeManager(db)
    return await mgr.create_knowledge(industry.id, req.title, req.content, req.category, req.tags, req.source)


@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = IndustryKnowledgeManager(db)
    if not await mgr.delete_knowledge(knowledge_id):
        raise HTTPException(404, "Knowledge entry not found")
    return {"message": "Deleted"}


# ─── AI Agents ───────────────────────────────────────────────────────────────

@router.get("/{slug}/agents", response_model=list[IndustryAgentResponse])
async def list_agents(slug: str, agent_type: str | None = None, db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    mgr = IndustryAgentManager(db)
    return await mgr.get_agents(industry.id, agent_type)


@router.post("/{slug}/agents", response_model=IndustryAgentResponse)
async def create_agent(slug: str, req: IndustryAgentCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    mgr = IndustryAgentManager(db)
    return await mgr.create_agent(industry.id, req.name, req.slug, req.agent_type, req.description, req.capabilities, req.system_prompt)


@router.post("/{slug}/agents/{agent_slug}/chat")
async def chat_with_agent(slug: str, agent_slug: str, query: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_industry(slug, db)
    mgr = IndustryAgentManager(db)
    return await mgr.query_agent(slug, query)


# ─── Workflows ───────────────────────────────────────────────────────────────

@router.get("/{slug}/workflows", response_model=list[IndustryWorkflowResponse])
async def list_workflows(slug: str, workflow_type: str | None = None, db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    query = select(IndustryWorkflow).where(IndustryWorkflow.industry_id == industry.id)
    if workflow_type:
        query = query.where(IndustryWorkflow.workflow_type == workflow_type)
    rows = await db.execute(query)
    return list(rows.scalars().all())


@router.post("/{slug}/workflows", response_model=IndustryWorkflowResponse)
async def create_workflow(slug: str, req: IndustryWorkflowCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    wf = IndustryWorkflow(
        industry_id=industry.id, name=req.name, description=req.description,
        workflow_type=req.workflow_type, steps=req.steps, trigger=req.trigger,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf


# ─── Templates ───────────────────────────────────────────────────────────────

@router.get("/{slug}/templates", response_model=list[IndustryTemplateResponse])
async def list_templates(slug: str, template_type: str | None = None, db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    engine = IndustryTemplateEngine(db)
    return await engine.get_templates(industry.id, template_type)


@router.post("/{slug}/templates", response_model=IndustryTemplateResponse)
async def create_template(slug: str, req: IndustryTemplateCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    engine = IndustryTemplateEngine(db)
    return await engine.create_template(industry.id, req.name, req.template_type, req.description, req.content, req.variables, req.category)


@router.post("/{slug}/templates/generate")
async def generate_from_template(slug: str, template_type: str, params: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = IndustryTemplateEngine(db)
    return await engine.generate_from_template(slug, template_type, params)


# ─── Compliance ──────────────────────────────────────────────────────────────

@router.get("/{slug}/compliance", response_model=list[ComplianceRuleResponse])
async def list_compliance_rules(slug: str, rule_type: str | None = None, db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    engine = IndustryComplianceEngine(db)
    return await engine.get_rules(industry.id, rule_type)


@router.post("/{slug}/compliance", response_model=ComplianceRuleResponse)
async def create_compliance_rule(slug: str, req: ComplianceRuleCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    engine = IndustryComplianceEngine(db)
    return await engine.create_rule(industry.id, req.name, req.rule_type, req.severity, req.description, req.condition, req.action)


@router.post("/{slug}/compliance/check")
async def check_compliance(slug: str, data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    engine = IndustryComplianceEngine(db)
    return await engine.check_compliance(industry.id, data)


# ─── Analytics ───────────────────────────────────────────────────────────────

@router.get("/{slug}/analytics")
async def get_industry_analytics(slug: str, period: str = "monthly", db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    rows = await db.execute(
        select(IndustryAnalytic)
        .where(IndustryAnalytic.industry_id == industry.id)
        .where(IndustryAnalytic.period == period)
        .order_by(IndustryAnalytic.created_at.desc())
    )
    return list(rows.scalars().all())


# ─── Dashboard ───────────────────────────────────────────────────────────────

@router.get("/{slug}/dashboard")
async def get_industry_dashboard(slug: str, db: AsyncSession = Depends(get_db)):
    industry = await _get_industry(slug, db)
    agent_count = (await db.execute(select(func.count(IndustryAgent.id)).where(IndustryAgent.industry_id == industry.id))).scalar() or 0
    workflow_count = (await db.execute(select(func.count(IndustryWorkflow.id)).where(IndustryWorkflow.industry_id == industry.id))).scalar() or 0
    kb_count = (await db.execute(select(func.count(IndustryKnowledgeBase.id)).where(IndustryKnowledgeBase.industry_id == industry.id))).scalar() or 0
    template_count = (await db.execute(select(func.count(IndustryTemplate.id)).where(IndustryTemplate.industry_id == industry.id))).scalar() or 0
    package_count = (await db.execute(select(func.count(SolutionPackage.id)).where(SolutionPackage.industry_id == industry.id))).scalar() or 0
    return {
        "industry": {"id": str(industry.id), "name": industry.name, "slug": industry.slug, "description": industry.description, "icon": industry.icon, "color": industry.color},
        "stats": {"agents": agent_count, "workflows": workflow_count, "knowledge_entries": kb_count, "templates": template_count, "packages": package_count},
    }


# ─── Seed Industries (Admin) ────────────────────────────────────────────────

@router.post("/seed")
async def seed_industries(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = IndustrySolutionBuilder(db)
    mgr = IndustryAgentManager(db)
    existing = await svc.list_industries()
    if len(existing) >= 7:
        return {"message": "Industries already seeded"}
    industries = [
        {"name": "NGO & Development", "slug": "ngo", "description": "AI solutions for NGOs, charities, and development organizations — grant writing, project management, monitoring & evaluation, and donor reporting.", "icon": "Heart", "color": "emerald", "sort_order": 1},
        {"name": "Education", "slug": "education", "description": "AI solutions for educational institutions — personalized tutoring, lesson planning, student assessment, and school administration.", "icon": "GraduationCap", "color": "blue", "sort_order": 2},
        {"name": "Healthcare", "slug": "healthcare", "description": "AI-powered healthcare administration support — patient information, appointment management, health education, and medical document organization.", "icon": "Stethoscope", "color": "red", "sort_order": 3},
        {"name": "Agriculture", "slug": "agriculture", "description": "AI solutions for farming and agribusiness — crop management, market intelligence, farm planning, and pest identification support.", "icon": "Sprout", "color": "green", "sort_order": 4},
        {"name": "Tourism & Hospitality", "slug": "tourism", "description": "AI solutions for travel, hotels, and hospitality — itinerary planning, guest services, booking management, and business intelligence.", "icon": "Compass", "color": "amber", "sort_order": 5},
        {"name": "Government & Public Services", "slug": "government", "description": "AI solutions for public sector — citizen services, document processing, service requests, and administrative automation.", "icon": "Landmark", "color": "indigo", "sort_order": 6},
        {"name": "Business", "slug": "business", "description": "Complete AI-powered business solutions — executive assistance, finance, HR, sales, marketing, customer support, and operations.", "icon": "Briefcase", "color": "violet", "sort_order": 7},
    ]
    for ind_data in industries:
        industry = await svc.create_industry(**ind_data)
        await mgr.create_agent(industry.id, f"{ind_data['name']} Assistant", f"{ind_data['slug']}-assistant", "general", f"Primary AI assistant for {ind_data['name']}")
    return {"message": f"Seeded {len(industries)} industries"}

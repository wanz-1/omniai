import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.v3_creation import (
    AIGeneratedProductResponse, DesignAssetResponse, DesignGenerateRequest,
    ProductIdeaResponse, StartupGenerateRequest, StartupProjectResponse,
)
from app.services.v3.creation_service import CreationEngineService

router = APIRouter()


@router.post("/startups", response_model=StartupProjectResponse)
async def create_startup(req: StartupGenerateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    return await svc.create_startup(current_user.id, req.name, req.description, req.industry)


@router.get("/startups", response_model=list[StartupProjectResponse])
async def list_startups(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    return await svc.list_startups(current_user.id)


@router.post("/startups/{startup_id}/business-plan")
async def generate_business_plan(startup_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    return await svc.generate_business_plan(startup_id)


@router.post("/startups/{startup_id}/products", response_model=AIGeneratedProductResponse)
async def generate_product(startup_id: uuid.UUID, product_type: str, name: str, description: str | None = None, platform: str = "web", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    product, _ = await svc.generate_product(startup_id, product_type, name, description, platform)
    return product


@router.post("/ideas", response_model=ProductIdeaResponse)
async def create_idea(title: str, description: str | None = None, industry: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    return await svc.create_product_idea(current_user.id, title, description, industry)


@router.post("/ideas/{idea_id}/validate")
async def validate_idea(idea_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    return await svc.validate_idea(idea_id)


@router.post("/designs", response_model=DesignAssetResponse)
async def generate_design(req: DesignGenerateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    return await svc.generate_design(current_user.id, req.name, req.asset_type, req.description, req.style, req.prompt)


@router.get("/designs", response_model=list[DesignAssetResponse])
async def list_designs(asset_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CreationEngineService(db)
    return await svc.list_designs(current_user.id, asset_type)

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.dependencies import get_db
from app.models.user import User

from app.schemas.v4_ecosystem import (
    EnterpriseIntegrationV4Response,
    SyncResponse,
    SyncRecordV4Response,
    AIAppDefinitionResponse,
    AIAppGenerateResponse,
    AppComponentV4Response,
    PublishedAppV4Response,
    ModelRegistryEntryV4Response,
    SdkReleaseV4Response,
    PluginDefinitionV4Response,
)
from app.services.v4.ecosystem_service import EcosystemService

router = APIRouter()


@router.post("/integrations", response_model=EnterpriseIntegrationV4Response)
async def create_integration(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.create_integration(current_user=current_user)


@router.get("/integrations", response_model=list[EnterpriseIntegrationV4Response])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.list_integrations(current_user=current_user)


@router.post("/integrations/{integration_id}/sync", response_model=SyncResponse)
async def sync_integration(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.sync_integration(
        integration_id=integration_id, current_user=current_user
    )


@router.get(
    "/integrations/{integration_id}/sync-history",
    response_model=list[SyncRecordV4Response],
)
async def get_sync_history(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.get_sync_history(
        integration_id=integration_id, current_user=current_user
    )


@router.post("/builder/apps", response_model=AIAppDefinitionResponse)
async def create_ai_app(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.create_ai_app(current_user=current_user)


@router.get("/builder/apps", response_model=list[AIAppDefinitionResponse])
async def list_ai_apps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.list_ai_apps(current_user=current_user)


@router.post("/builder/apps/{app_id}/generate", response_model=AIAppGenerateResponse)
async def generate_app_from_prompt(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    result = await svc.generate_from_prompt(app_id=app_id)
    if not isinstance(result, dict):
        raise HTTPException(404, "AI app not found or has no prompt")
    return result


@router.post(
    "/builder/apps/{app_id}/components", response_model=AppComponentV4Response
)
async def add_app_component(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.add_app_component(app_id=app_id, current_user=current_user)


@router.post(
    "/builder/apps/{app_id}/publish", response_model=PublishedAppV4Response
)
async def publish_ai_app(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.publish_ai_app(app_id=app_id, current_user=current_user)


@router.post("/models/register", response_model=ModelRegistryEntryV4Response)
async def register_model(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.register_model(current_user=current_user)


@router.get("/models/registered", response_model=list[ModelRegistryEntryV4Response])
async def list_registered_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.list_registered_models(current_user=current_user)


@router.get("/sdks", response_model=list[SdkReleaseV4Response])
async def list_sdk_releases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.list_sdk_releases(current_user=current_user)


@router.post("/plugins", response_model=PluginDefinitionV4Response)
async def create_plugin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.create_plugin(current_user=current_user)


@router.get("/plugins", response_model=list[PluginDefinitionV4Response])
async def list_plugins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = EcosystemService(db)
    return await svc.list_plugins(current_user=current_user)

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v4_cloud import (
    AppCategoryResponse,
    AppInstallationResponse,
    AppListingResponse,
    AppPurchaseResponse,
    AppQueryResponse,
    BackupRecordV4Response,
    DisasterRecoveryPlanResponse,
    RegionalDeploymentResponse,
    TenantEnvironmentResponse,
    UsageMetricResponse,
    WorkflowInstallationV4Response,
    WorkflowTemplateResponse,
)
from app.services.v4.cloud_service import CloudPlatformService

router = APIRouter()


@router.post("/environments", response_model=TenantEnvironmentResponse)
async def create_environment(
    organization_id: uuid.UUID,
    name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    environment_type: str = "development",
    region: str | None = None,
):
    svc = CloudPlatformService(db)
    return await svc.create_environment(organization_id, name, environment_type, region)


@router.get("/environments", response_model=list[TenantEnvironmentResponse])
async def list_environments(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_environments(organization_id)


@router.get("/environments/{env_id}", response_model=TenantEnvironmentResponse)
async def get_environment(
    env_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.get_environment(env_id)


@router.patch("/environments/{env_id}", response_model=TenantEnvironmentResponse)
async def update_environment(
    env_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    name: str | None = None,
    environment_type: str | None = None,
    region: str | None = None,
    status: str | None = None,
):
    svc = CloudPlatformService(db)
    return await svc.update_environment(env_id, name, environment_type, region, status)


@router.delete("/environments/{env_id}")
async def delete_environment(
    env_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    await svc.delete_environment(env_id)
    return {"message": "Environment deleted successfully"}


@router.post("/environments/{tenant_id}/deployments", response_model=RegionalDeploymentResponse)
async def create_deployment(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.create_deployment(tenant_id)


@router.get("/environments/{tenant_id}/deployments", response_model=list[RegionalDeploymentResponse])
async def list_deployments(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_deployments(tenant_id)


@router.post("/environments/{tenant_id}/backups", response_model=BackupRecordV4Response)
async def create_backup(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.create_backup(tenant_id)


@router.get("/environments/{tenant_id}/backups", response_model=list[BackupRecordV4Response])
async def list_backups(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_backups(tenant_id)


@router.post("/environments/{tenant_id}/dr-plans", response_model=DisasterRecoveryPlanResponse)
async def create_dr_plan(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.create_dr_plan(tenant_id)


@router.get("/environments/{tenant_id}/dr-plans", response_model=list[DisasterRecoveryPlanResponse])
async def list_dr_plans(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_dr_plans(tenant_id)


@router.post("/environments/{tenant_id}/metrics", response_model=UsageMetricResponse)
async def record_metric(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.record_metric(tenant_id)


@router.get("/environments/{tenant_id}/metrics", response_model=list[UsageMetricResponse])
async def list_metrics(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_metrics(tenant_id)


@router.post("/apps/categories", response_model=AppCategoryResponse)
async def create_app_category(
    name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    description: str | None = None,
):
    svc = CloudPlatformService(db)
    return await svc.create_app_category(name, description)


@router.get("/apps/categories", response_model=list[AppCategoryResponse])
async def list_app_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_app_categories()


@router.post("/apps/listings", response_model=AppListingResponse)
async def create_app_listing(
    name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    description: str | None = None,
    category_id: uuid.UUID | None = None,
):
    svc = CloudPlatformService(db)
    return await svc.create_app_listing(name, description, category_id)


@router.get("/apps/listings", response_model=list[AppListingResponse])
async def list_app_listings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_app_listings()


@router.get("/apps/listings/search", response_model=AppQueryResponse)
async def search_app_listings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., description="Search query"),
):
    svc = CloudPlatformService(db)
    return await svc.search_app_listings(q)


@router.post("/apps/install", response_model=AppInstallationResponse)
async def install_app(
    app_listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    environment_id: uuid.UUID | None = None,
):
    svc = CloudPlatformService(db)
    return await svc.install_app(current_user.id, app_listing_id, environment_id)


@router.get("/apps/installations", response_model=list[AppInstallationResponse])
async def list_app_installations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_app_installations(current_user.id)


@router.post("/apps/purchase", response_model=AppPurchaseResponse)
async def purchase_app(
    app_listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.purchase_app(current_user.id, app_listing_id)


@router.post("/workflows/templates", response_model=WorkflowTemplateResponse)
async def create_workflow_template(
    name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    description: str | None = None,
    category_id: uuid.UUID | None = None,
):
    svc = CloudPlatformService(db)
    return await svc.create_workflow_template(name, description, category_id)


@router.get("/workflows/templates", response_model=list[WorkflowTemplateResponse])
async def list_workflow_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_workflow_templates()


@router.post("/workflows/install", response_model=WorkflowInstallationV4Response)
async def install_workflow(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    environment_id: uuid.UUID | None = None,
):
    svc = CloudPlatformService(db)
    return await svc.install_workflow(current_user.id, template_id, environment_id)


@router.get("/workflows/installations", response_model=list[WorkflowInstallationV4Response])
async def list_workflow_installations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CloudPlatformService(db)
    return await svc.list_workflow_installations(current_user.id)

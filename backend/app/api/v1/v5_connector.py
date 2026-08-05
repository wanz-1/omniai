import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v5_connector_platform import (
    ConnectorDefinitionResponse, ConnectorIntegrationResponse,
    SyncJobResponse, WebhookEventResponse, ConnectorLogResponse,
    ConnectorApiKeyResponse, CustomConnectorEndpointResponse,
    InstallConnectorRequest, CreateCustomConnectorRequest,
    AuthenticateConnectorRequest, SyncConnectorRequest,
    RegisterWebhookRequest, CreateApiKeyRequest,
    ConnectorQueryRequest, ConnectorDashboardResponse,
)
from app.services.connector_platform.connector_manager import ConnectorManager
from app.services.connector_platform.authentication_service import AuthenticationService
from app.services.connector_platform.sync_engine import SyncEngine
from app.services.connector_platform.webhook_manager import WebhookManager
from app.services.connector_platform.api_gateway import ApiGateway
from app.services.connector_platform.connector_sdk import ConnectorSDK
from app.services.connector_platform.marketplace_service import MarketplaceService
from app.services.connector_platform.monitoring_service import MonitoringService

router = APIRouter()


def _ensure_org_access(integration, current_user: User) -> None:
    org_id = current_user.organization_id or current_user.id
    if integration.organization_id and str(integration.organization_id) != str(org_id):
        raise HTTPException(status_code=404, detail="Integration not found")


@router.get("/definitions", response_model=list[ConnectorDefinitionResponse])
async def list_connector_definitions(
    category: str | None = None,
    connector_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    mgr = ConnectorManager(db)
    return await mgr.list_definitions(category, connector_type)


@router.post("/install", response_model=ConnectorIntegrationResponse)
async def install_connector(
    req: InstallConnectorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = ConnectorManager(db)
    return await mgr.install_connector(
        current_user.organization_id or current_user.id,
        req.connector_id, req.name, req.config, current_user.id,
    )


@router.get("/integrations", response_model=list[ConnectorIntegrationResponse])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = ConnectorManager(db)
    return await mgr.list_integrations(current_user.organization_id or current_user.id)


@router.get("/integrations/{integration_id}", response_model=ConnectorIntegrationResponse)
async def get_integration(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = ConnectorManager(db)
    integ = await mgr.get_integration(integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    return integ


@router.delete("/integrations/{integration_id}")
async def uninstall_connector(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = ConnectorManager(db)
    integ = await mgr.get_integration(integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    result = await mgr.uninstall_connector(integration_id)
    return {"status": "uninstalled" if result else "not_found"}


@router.post("/authenticate")
async def authenticate_connector(
    req: AuthenticateConnectorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    integ = await ConnectorManager(db).get_integration(req.integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    return await auth.authenticate(req.integration_id, req.auth_data)


@router.get("/oauth/authorize/{integration_id}")
async def get_oauth_authorization_url(
    integration_id: uuid.UUID,
    redirect_uri: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    integ = await ConnectorManager(db).get_integration(integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    return await auth.get_authorization_url(integration_id, redirect_uri)


@router.post("/oauth/callback/{integration_id}")
async def handle_oauth_callback(
    integration_id: uuid.UUID,
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    integ = await ConnectorManager(db).get_integration(integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    return await auth.handle_oauth_callback(integration_id, code, state)


@router.post("/oauth/refresh/{credential_id}")
async def refresh_oauth_token(
    credential_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    return await auth.refresh_access_token(credential_id)


@router.post("/credentials/rotate/{credential_id}")
async def rotate_credentials(
    credential_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    return await auth.rotate_credentials(credential_id)


@router.post("/api-keys", response_model=ConnectorApiKeyResponse)
async def create_api_key(
    req: CreateApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    return await auth.create_api_key(
        current_user.organization_id or current_user.id,
        req.name, req.scopes, current_user.id,
    )


@router.get("/api-keys", response_model=list[ConnectorApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    return await auth.list_api_keys(current_user.organization_id or current_user.id)


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth = AuthenticationService(db)
    result = await auth.revoke_api_key(key_id)
    return {"status": "revoked" if result else "not_found"}


@router.post("/sync", response_model=SyncJobResponse)
async def start_sync(
    req: SyncConnectorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = SyncEngine(db)
    return await engine.start_sync(req.integration_id, req.sync_type)


@router.post("/sync/{job_id}/complete", response_model=SyncJobResponse)
async def complete_sync(
    job_id: uuid.UUID,
    stats: dict | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = SyncEngine(db)
    job = await engine.complete_sync(job_id, stats)
    return job


@router.get("/sync/jobs", response_model=list[SyncJobResponse])
async def list_sync_jobs(
    integration_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = SyncEngine(db)
    return await engine.list_sync_jobs(
        integration_id=integration_id,
        org_id=current_user.organization_id or current_user.id,
    )


@router.post("/sync/run/{integration_id}")
async def run_sync(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = SyncEngine(db)
    integ = await ConnectorManager(db).get_integration(integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    return await engine.run_sync(integration_id)


@router.get("/sync/summary")
async def get_sync_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    engine = SyncEngine(db)
    return await engine.get_sync_summary(current_user.organization_id or current_user.id)


@router.post("/webhooks/register")
async def register_webhook(
    req: RegisterWebhookRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = WebhookManager(db)
    integ = await ConnectorManager(db).get_integration(req.integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    return await mgr.register_webhook(req.integration_id, req.event_type, req.target_url, req.secret)


@router.post("/webhooks/receive", response_model=WebhookEventResponse)
async def receive_webhook(
    source: str, event_type: str, payload: dict,
    org_id: uuid.UUID | None = None,
    integration_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = WebhookManager(db)
    return await mgr.receive_event(
        org_id or current_user.organization_id or current_user.id,
        integration_id, source, event_type, payload,
    )


@router.post("/webhooks/{event_id}/process")
async def process_webhook_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = WebhookManager(db)
    return await mgr.process_event(event_id)


@router.get("/webhooks/events", response_model=list[WebhookEventResponse])
async def list_webhook_events(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = WebhookManager(db)
    return await mgr.list_events(current_user.organization_id or current_user.id, status)


@router.post("/custom/create", response_model=CustomConnectorEndpointResponse)
async def create_custom_connector(
    req: CreateCustomConnectorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gw = ApiGateway(db)
    return await gw.create_custom_connector(
        current_user.organization_id or current_user.id,
        req.name, req.api_type, req.base_url, req.auth_method,
        req.headers, req.endpoints, req.rate_limit, current_user.id,
    )


@router.get("/custom", response_model=list[CustomConnectorEndpointResponse])
async def list_custom_connectors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gw = ApiGateway(db)
    return await gw.list_custom_connectors(current_user.organization_id or current_user.id)


@router.delete("/custom/{endpoint_id}")
async def delete_custom_connector(
    endpoint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gw = ApiGateway(db)
    result = await gw.delete_custom_connector(endpoint_id)
    return {"status": "deleted" if result else "not_found"}


@router.post("/custom/{endpoint_id}/execute")
async def execute_custom_api(
    endpoint_id: uuid.UUID,
    action: str,
    params: dict | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gw = ApiGateway(db)
    return await gw.execute_custom_api(endpoint_id, action, params)


@router.post("/query")
async def query_connector(
    req: ConnectorQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = ConnectorManager(db)
    integ = await mgr.get_integration(req.integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")
    _ensure_org_access(integ, current_user)
    return await mgr.query_connector(req.integration_id, req.action, req.params)


@router.post("/sdk/generate")
async def generate_connector_code(
    spec: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sdk = ConnectorSDK(db)
    return await sdk.generate_connector_code(spec)


@router.post("/sdk/validate/{connector_id}")
async def validate_connector(
    connector_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sdk = ConnectorSDK(db)
    return await sdk.validate_connector(connector_id)


@router.post("/sdk/test/{integration_id}")
async def test_connection(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sdk = ConnectorSDK(db)
    return await sdk.test_connection(integration_id)


@router.get("/marketplace")
async def list_marketplace(
    category: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    marketplace = MarketplaceService(db)
    return await marketplace.list_marketplace_items(category, search)


@router.get("/marketplace/{item_id}")
async def get_marketplace_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    marketplace = MarketplaceService(db)
    return await marketplace.get_marketplace_item(item_id)


@router.get("/logs", response_model=list[ConnectorLogResponse])
async def get_connector_logs(
    integration_id: uuid.UUID | None = None,
    level: str | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mon = MonitoringService(db)
    return await mon.get_logs(
        integration_id=integration_id,
        org_id=current_user.organization_id or current_user.id,
        level=level, limit=limit,
    )


@router.post("/permissions/grant")
async def grant_permission(
    integration_id: uuid.UUID,
    principal_type: str,
    principal_id: uuid.UUID,
    permission: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mon = MonitoringService(db)
    return await mon.grant_permission(
        integration_id, current_user.organization_id or current_user.id,
        principal_type, principal_id, permission, current_user.id,
    )


@router.delete("/permissions/{permission_id}")
async def revoke_permission(
    permission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mon = MonitoringService(db)
    result = await mon.revoke_permission(permission_id)
    return {"status": "revoked" if result else "not_found"}


@router.get("/permissions/{integration_id}")
async def list_permissions(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mon = MonitoringService(db)
    return await mon.list_permissions(integration_id)


@router.get("/analytics")
async def get_connector_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mon = MonitoringService(db)
    return await mon.get_analytics(current_user.organization_id or current_user.id)


@router.post("/analytics/logs/analyze")
async def analyze_connector_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mon = MonitoringService(db)
    analysis = await mon.analyze_logs(current_user.organization_id or current_user.id)
    return {"analysis": analysis}


@router.get("/dashboard", response_model=ConnectorDashboardResponse)
async def get_connector_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = ConnectorManager(db)
    return await mgr.get_dashboard(current_user.organization_id or current_user.id)

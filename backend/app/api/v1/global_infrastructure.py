import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.global_infrastructure import (
    AIModelRegistry,
    BackupRecord,
    ClusterDeployment,
    DeveloperApiKey,
    InfrastructureRegion,
    SecurityEvent,
    ServiceDeployment,
)
from app.models.user import User
from app.schemas.global_infrastructure import (
    BackupRecordResponse,
    ClusterResponse,
    ComplianceReportResponse,
    DataResidencyResponse,
    DeveloperApiKeyCreate,
    DeveloperApiKeyResponse,
    ModelRegistryResponse,
    ModelRouteRequest,
    ModelRouteResponse,
    MonitoringMetricResponse,
    OrganizationPolicyResponse,
    RegionResponse,
    SecurityEventResponse,
    ServiceDeploymentResponse,
)
from app.services.infra.backup_service import InfraBackupService
from app.services.infra.compliance_engine import InfraComplianceEngine
from app.services.infra.deployment_manager import InfraDeploymentManager
from app.services.infra.monitoring_service import InfraMonitoringService
from app.services.infra.scaling_engine import InfraScalingEngine
from app.services.infra.security_manager import InfraSecurityManager

router = APIRouter()


# ─── Regions ─────────────────────────────────────────────────────────────────

@router.get("/regions", response_model=list[RegionResponse])
async def list_regions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    return await mgr.list_regions()


@router.post("/regions", response_model=RegionResponse)
async def create_region(name: str, slug: str, provider: str, description: str | None = None, location: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    return await mgr.create_region(name, slug, provider, description, location)


@router.get("/regions/{region_id}", response_model=RegionResponse)
async def get_region(region_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    region = await mgr.get_region(region_id)
    if not region:
        raise HTTPException(404, "Region not found")
    return region


# ─── Clusters ────────────────────────────────────────────────────────────────

@router.get("/clusters", response_model=list[ClusterResponse])
async def list_clusters(region_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    return await mgr.list_clusters(region_id)


@router.post("/clusters", response_model=ClusterResponse)
async def create_cluster(region_id: uuid.UUID, name: str, cluster_type: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    return await mgr.create_cluster(region_id, name, cluster_type)


@router.post("/clusters/{cluster_id}/health")
async def update_cluster_health(cluster_id: uuid.UUID, status: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    cluster = await mgr.update_cluster_health(cluster_id, status)
    if not cluster:
        raise HTTPException(404, "Cluster not found")
    return {"message": f"Health updated to {status}"}


# ─── Services ────────────────────────────────────────────────────────────────

@router.get("/services", response_model=list[ServiceDeploymentResponse])
async def list_services(cluster_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    return await mgr.list_services(cluster_id)


@router.post("/services", response_model=ServiceDeploymentResponse)
async def deploy_service(cluster_id: uuid.UUID, service_name: str, service_type: str, version: str, replicas: int = 1, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    return await mgr.deploy_service(cluster_id, service_name, service_type, version, replicas)


@router.post("/services/{service_id}/scale")
async def scale_service(service_id: uuid.UUID, target_replicas: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    svc = await mgr.scale_service(service_id, target_replicas)
    if not svc:
        raise HTTPException(404, "Service not found")
    return {"message": f"Scaled to {target_replicas} replicas"}


# ─── Model Registry ──────────────────────────────────────────────────────────

@router.get("/models", response_model=list[ModelRegistryResponse])
async def list_models(model_type: str | None = None, provider: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraScalingEngine(db)
    return await engine.list_models(model_type, provider)


@router.post("/models", response_model=ModelRegistryResponse)
async def register_model(name: str, provider: str, model_id: str, model_type: str, cost: float = 0.0, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraScalingEngine(db)
    return await engine.register_model(name, provider, model_id, model_type, cost=cost)


@router.post("/models/route", response_model=ModelRouteResponse)
async def route_model(req: ModelRouteRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraScalingEngine(db)
    return await engine.route_model(req.task, req.complexity, req.max_cost, req.preferred_provider, req.required_capabilities)


# ─── Security ────────────────────────────────────────────────────────────────

@router.get("/security/events", response_model=list[SecurityEventResponse])
async def list_security_events(event_type: str | None = None, severity: str | None = None, resolved: bool | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraSecurityManager(db)
    return await mgr.list_events(event_type, severity, resolved)


@router.post("/security/events", response_model=SecurityEventResponse)
async def log_security_event(event_type: str, severity: str, description: str | None = None, source: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraSecurityManager(db)
    return await mgr.log_event(event_type, severity, description, source, user_id=current_user.id)


@router.post("/security/events/{event_id}/resolve")
async def resolve_security_event(event_id: uuid.UUID, action_taken: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraSecurityManager(db)
    event = await mgr.resolve_event(event_id, action_taken)
    if not event:
        raise HTTPException(404, "Event not found")
    return {"message": "Resolved"}


@router.get("/security/summary")
async def security_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraSecurityManager(db)
    return await mgr.get_security_summary()


# ─── Monitoring ──────────────────────────────────────────────────────────────

@router.get("/monitoring/metrics", response_model=list[MonitoringMetricResponse])
async def get_metrics(metric_name: str | None = None, metric_type: str | None = None, region_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraMonitoringService(db)
    return await svc.get_metrics(metric_name, metric_type, region_id)


@router.post("/monitoring/metrics")
async def record_metric(metric_name: str, metric_value: float, metric_type: str, unit: str | None = None, source: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraMonitoringService(db)
    m = await svc.record_metric(metric_name, metric_value, metric_type, unit, source)
    return {"id": str(m.id), "metric_name": m.metric_name, "metric_value": m.metric_value}


@router.get("/monitoring/health")
async def system_health(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraMonitoringService(db)
    return await svc.get_system_health()


@router.get("/monitoring/uptime")
async def api_uptime(days: int = 30, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraMonitoringService(db)
    return await svc.get_api_uptime(days)


# ─── Backups ─────────────────────────────────────────────────────────────────

@router.get("/backups", response_model=list[BackupRecordResponse])
async def list_backups(backup_type: str | None = None, status: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraBackupService(db)
    return await svc.list_backups(backup_type, status)


@router.post("/backups", response_model=BackupRecordResponse)
async def create_backup(name: str, backup_type: str, target: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraBackupService(db)
    return await svc.create_backup(name, backup_type, target)


@router.get("/backups/{backup_id}", response_model=BackupRecordResponse)
async def get_backup(backup_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraBackupService(db)
    backup = await svc.get_backup(backup_id)
    if not backup:
        raise HTTPException(404, "Backup not found")
    return backup


@router.post("/backups/{backup_id}/complete")
async def complete_backup(backup_id: uuid.UUID, size_bytes: int, location: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraBackupService(db)
    backup = await svc.complete_backup(backup_id, size_bytes, location)
    if not backup:
        raise HTTPException(404, "Backup not found")
    return {"message": "Backup completed"}


@router.get("/backups/summary")
async def backup_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = InfraBackupService(db)
    return await svc.get_backup_summary()


# ─── Compliance & Policies ───────────────────────────────────────────────────

@router.get("/policies/{organization_id}", response_model=list[OrganizationPolicyResponse])
async def list_policies(organization_id: uuid.UUID, policy_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraComplianceEngine(db)
    return await engine.list_policies(organization_id, policy_type)


@router.post("/policies/{organization_id}")
async def create_policy(organization_id: uuid.UUID, policy_type: str, name: str, severity: str = "medium", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraComplianceEngine(db)
    return await engine.create_policy(organization_id, policy_type, name, severity=severity)


@router.get("/compliance/reports", response_model=list[ComplianceReportResponse])
async def list_reports(report_type: str | None = None, organization_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraComplianceEngine(db)
    return await engine.list_reports(report_type, organization_id)


@router.post("/compliance/reports")
async def create_report(report_type: str, title: str, organization_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraComplianceEngine(db)
    return await engine.create_report(report_type, title, organization_id)


@router.post("/compliance/reports/{report_id}/generate")
async def generate_report(report_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraComplianceEngine(db)
    result = await engine.generate_report_ai(report_id)
    if not result:
        raise HTTPException(404, "Report not found")
    return result


# ─── Data Residency ──────────────────────────────────────────────────────────

@router.post("/data-residency/{organization_id}")
async def configure_data_residency(organization_id: uuid.UUID, region_id: uuid.UUID, data_type: str, retention_days: int = 365, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraComplianceEngine(db)
    return await engine.configure_data_residency(organization_id, region_id, data_type, retention_days)


@router.get("/data-residency/{organization_id}", response_model=list[DataResidencyResponse])
async def list_data_residency(organization_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    engine = InfraComplianceEngine(db)
    return await engine.list_data_residency(organization_id)


# ─── Developer API Keys ──────────────────────────────────────────────────────

@router.post("/api-keys/{organization_id}", response_model=DeveloperApiKeyResponse)
async def create_api_key(organization_id: uuid.UUID, req: DeveloperApiKeyCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import hashlib
    import secrets
    key = f"omni_{secrets.token_hex(24)}"
    key_prefix = key[:10]
    dev_key = DeveloperApiKey(
        organization_id=organization_id, name=req.name,
        key_prefix=key_prefix, key_hash=hashlib.sha512(key.encode()).hexdigest(),
        scopes=req.scopes or [], rate_limit=req.rate_limit,
        expires_at=req.expires_at,
    )
    db.add(dev_key)
    await db.commit()
    await db.refresh(dev_key)
    return dev_key


@router.get("/api-keys/{organization_id}", response_model=list[DeveloperApiKeyResponse])
async def list_api_keys(organization_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        select(DeveloperApiKey).where(DeveloperApiKey.organization_id == organization_id)
    )
    return list(rows.scalars().all())


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    key = await db.get(DeveloperApiKey, key_id)
    if not key:
        raise HTTPException(404, "API key not found")
    await db.delete(key)
    await db.commit()
    return {"message": "Deleted"}


# ─── Dashboard ───────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def infrastructure_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    region_count = (await db.execute(select(func.count(InfrastructureRegion.id)))).scalar() or 0
    cluster_count = (await db.execute(select(func.count(ClusterDeployment.id)))).scalar() or 0
    svc_count = (await db.execute(select(func.count(ServiceDeployment.id)))).scalar() or 0
    model_count = (await db.execute(select(func.count(AIModelRegistry.id)))).scalar() or 0
    event_count = (await db.execute(select(func.count(SecurityEvent.id)).where(SecurityEvent.is_resolved.is_(False)))).scalar() or 0
    backup_count = (await db.execute(select(func.count(BackupRecord.id)))).scalar() or 0
    return {
        "stats": {
            "regions": region_count, "clusters": cluster_count,
            "services": svc_count, "models": model_count,
            "unresolved_events": event_count, "backups": backup_count,
        }
    }


# ─── Seed ────────────────────────────────────────────────────────────────────

@router.post("/seed")
async def seed_infrastructure(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = InfraDeploymentManager(db)
    existing = await mgr.list_regions()
    if len(existing) >= 4:
        return {"message": "Infrastructure already seeded"}
    regions = [
        {"name": "North America", "slug": "na", "provider": "aws", "description": "US East (N. Virginia) region", "location": "us-east-1", "priority": 1},
        {"name": "Europe", "slug": "eu", "provider": "aws", "description": "EU (Frankfurt) region", "location": "eu-central-1", "priority": 2},
        {"name": "Africa", "slug": "af", "provider": "aws", "description": "Africa (Cape Town) region", "location": "af-south-1", "priority": 3},
        {"name": "Asia", "slug": "as", "provider": "aws", "description": "Asia Pacific (Singapore) region", "location": "ap-southeast-1", "priority": 4},
    ]
    engine = InfraScalingEngine(db)
    for r in regions:
        region = await mgr.create_region(**r)
        cluster = await mgr.create_cluster(region.id, f"{r['name']}-cluster", "kubernetes")
        await mgr.deploy_service(cluster.id, "api-gateway", "gateway", "1.0.0", 3)
        await mgr.deploy_service(cluster.id, "ai-service", "ml", "1.0.0", 5)
        await mgr.deploy_service(cluster.id, "agent-service", "compute", "1.0.0", 3)
    models = [
        {"name": "GPT-4o", "provider": "openai", "model_id": "gpt-4o", "model_type": "chat", "capabilities": ["reasoning", "vision", "code"], "cost": 0.01, "latency_p50": 0.8, "latency_p99": 3.0, "max_tokens": 128000},
        {"name": "GPT-4o-mini", "provider": "openai", "model_id": "gpt-4o-mini", "model_type": "chat", "capabilities": ["code"], "cost": 0.001, "latency_p50": 0.3, "latency_p99": 1.0, "max_tokens": 128000},
        {"name": "Claude 3.5 Sonnet", "provider": "anthropic", "model_id": "claude-3-5-sonnet", "model_type": "chat", "capabilities": ["reasoning", "code", "analysis"], "cost": 0.015, "latency_p50": 1.0, "latency_p99": 4.0, "max_tokens": 200000},
        {"name": "Claude 3 Haiku", "provider": "anthropic", "model_id": "claude-3-haiku", "model_type": "chat", "capabilities": ["fast"], "cost": 0.002, "latency_p50": 0.2, "latency_p99": 0.8, "max_tokens": 200000},
    ]
    for m in models:
        await engine.register_model(**m)
    return {"message": f"Seeded {len(regions)} regions with clusters and {len(models)} AI models"}

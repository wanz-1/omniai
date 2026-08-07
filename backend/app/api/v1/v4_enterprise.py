import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v4_enterprise import (
    AgentApprovalRequestResponse,
    AIMonitoringEventV4Response,
    AIPolicyResponse,
    EnterpriseAnalyticsV4Response,
    KnowledgeConnectorResponse,
    ObservabilityDashboardResponse,
    PolicyCheckRequest,
    PolicyCheckResponse,
)
from app.services.v4.enterprise_service import EnterpriseService

router = APIRouter()


@router.post("/knowledge/connectors", response_model=KnowledgeConnectorResponse)
async def create_connector(organization_id: uuid.UUID, name: str, connector_type: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.create_connector(organization_id, name, connector_type)


@router.get("/knowledge/connectors", response_model=list[KnowledgeConnectorResponse])
async def list_connectors(organization_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.list_connectors(organization_id)


@router.post("/knowledge/connectors/{connector_id}/sync", response_model=KnowledgeConnectorResponse)
async def sync_connector(connector_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.sync_connector(connector_id)


@router.post("/knowledge/search")
async def search_knowledge(organization_id: uuid.UUID, query_text: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.search_knowledge(organization_id, query_text)


@router.post("/governance/policies", response_model=AIPolicyResponse)
async def create_policy(organization_id: uuid.UUID, name: str, policy_type: str, severity: str = "medium", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.create_policy(organization_id, name, policy_type, severity=severity)


@router.get("/governance/policies", response_model=list[AIPolicyResponse])
async def list_policies(organization_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.list_policies(organization_id)


@router.post("/governance/check", response_model=PolicyCheckResponse)
async def check_policy(req: PolicyCheckRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.check_policy(req.policy_type, req.resource_type, req.action, req.context)


@router.post("/governance/approvals", response_model=AgentApprovalRequestResponse)
async def create_approval(organization_id: uuid.UUID, agent_id: uuid.UUID, agent_name: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.create_approval_request(organization_id, agent_id, agent_name, current_user.id)


@router.patch("/governance/approvals/{request_id}", response_model=AgentApprovalRequestResponse)
async def review_approval(request_id: uuid.UUID, status: str, notes: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.review_approval(request_id, status, current_user.id, notes)


@router.post("/observability/events", response_model=AIMonitoringEventV4Response)
async def record_event(organization_id: uuid.UUID, event_type: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.record_monitoring_event(organization_id, event_type)


@router.get("/observability/events", response_model=list[AIMonitoringEventV4Response])
async def list_events(organization_id: uuid.UUID, event_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.get_monitoring_events(organization_id, event_type)


@router.post("/observability/dashboards", response_model=ObservabilityDashboardResponse)
async def create_dashboard(organization_id: uuid.UUID, name: str, dashboard_type: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.create_dashboard(organization_id, name, dashboard_type)


@router.get("/observability/dashboards", response_model=list[ObservabilityDashboardResponse])
async def list_dashboards(organization_id: uuid.UUID, dashboard_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.list_dashboards(organization_id, dashboard_type)


@router.post("/analytics/records", response_model=EnterpriseAnalyticsV4Response)
async def create_analytic(organization_id: uuid.UUID, metric_category: str, metric_name: str, metric_value: float, period: str = "daily", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.record_analytics(organization_id, metric_category, metric_name, metric_value, period=period)


@router.get("/analytics/records", response_model=list[EnterpriseAnalyticsV4Response])
async def list_analytics(organization_id: uuid.UUID, metric_category: str | None = None, period: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = EnterpriseService(db)
    return await svc.get_analytics(organization_id, metric_category, period)

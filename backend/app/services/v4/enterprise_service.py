from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v4_enterprise import (
    KnowledgeConnector, EnterpriseDocument,
    AIPolicy, AgentApprovalRequest, AIMonitoringEventV4, ObservabilityDashboard,
    EnterpriseAnalyticsV4,
)
from app.services.ai_service import ai_service


class EnterpriseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -- Knowledge Hub --
    async def create_connector(self, organization_id, name, connector_type, config=None):
        conn = KnowledgeConnector(organization_id=organization_id, name=name, connector_type=connector_type, config=config or {}, status="configured")
        self.db.add(conn); await self.db.commit(); await self.db.refresh(conn); return conn

    async def list_connectors(self, organization_id):
        rows = await self.db.execute(select(KnowledgeConnector).where(KnowledgeConnector.organization_id == organization_id))
        return list(rows.scalars().all())

    async def sync_connector(self, connector_id):
        conn = await self.db.get(KnowledgeConnector, connector_id)
        if not conn: return None
        conn.last_sync_at = func.now(); conn.status = "syncing"
        await self.db.commit()
        conn.status = "synced"; conn.last_sync_at = func.now()
        await self.db.commit(); await self.db.refresh(conn); return conn

    async def search_knowledge(self, organization_id, query_text):
        rows = await self.db.execute(
            select(EnterpriseDocument).where(EnterpriseDocument.organization_id == organization_id).limit(20)
        )
        docs = list(rows.scalars().all())
        prompt = f"Query: {query_text}\n\nSearch through enterprise documents. List relevant documents and summarize what they contain."
        result = await ai_service.complete(prompt)
        return {"response": result, "documents": [{"id": str(d.id), "title": d.title, "url": d.url} for d in docs]}

    # -- Governance --
    async def create_policy(self, organization_id, name, policy_type, rules=None, severity="medium", created_by=None):
        policy = AIPolicy(organization_id=organization_id, name=name, policy_type=policy_type, rules=rules or {}, severity=severity, created_by=created_by)
        self.db.add(policy); await self.db.commit(); await self.db.refresh(policy); return policy

    async def list_policies(self, organization_id):
        rows = await self.db.execute(select(AIPolicy).where(AIPolicy.organization_id == organization_id))
        return list(rows.scalars().all())

    async def check_policy(self, organization_id, policy_type, resource_type, action, context=None):
        rows = await self.db.execute(select(AIPolicy).where(AIPolicy.organization_id == organization_id, AIPolicy.policy_type == policy_type, AIPolicy.is_active == True))
        policies = list(rows.scalars().all())
        for p in policies:
            rules = p.rules or {}
            if resource_type in rules.get("restricted_resources", []):
                return {"allowed": False, "policy_name": p.name, "reason": f"Resource type '{resource_type}' is restricted", "required_approvals": rules.get("requires_approval", [])}
        return {"allowed": True, "policy_name": "default", "reason": "No matching restrictions", "required_approvals": []}

    async def create_approval_request(self, organization_id, agent_id, agent_name, requested_by, capabilities=None, justification=None):
        req = AgentApprovalRequest(organization_id=organization_id, agent_id=agent_id, agent_name=agent_name, requested_by=requested_by, capabilities=capabilities or [], justification=justification, status="pending")
        self.db.add(req); await self.db.commit(); await self.db.refresh(req); return req

    async def review_approval(self, request_id, status, reviewer_id, notes=None):
        req = await self.db.get(AgentApprovalRequest, request_id)
        if not req: return None
        req.status = status; req.reviewed_by = reviewer_id; req.review_notes = notes; req.reviewed_at = func.now()
        await self.db.commit(); await self.db.refresh(req); return req

    # -- Observability --
    async def record_monitoring_event(self, organization_id, event_type, model_id=None, model_provider=None, latency_ms=0.0, cost=0.0, tokens_input=0, tokens_output=0, status="success", **kwargs):
        event = AIMonitoringEventV4(organization_id=organization_id, event_type=event_type, model_id=model_id, model_provider=model_provider, latency_ms=latency_ms, cost=cost, tokens_input=tokens_input, tokens_output=tokens_output, status=status, **kwargs)
        self.db.add(event); await self.db.commit(); await self.db.refresh(event); return event

    async def get_monitoring_events(self, organization_id, event_type=None, limit=100):
        q = select(AIMonitoringEventV4).where(AIMonitoringEventV4.organization_id == organization_id)
        if event_type: q = q.where(AIMonitoringEventV4.event_type == event_type)
        q = q.order_by(AIMonitoringEventV4.recorded_at.desc()).limit(limit)
        rows = await self.db.execute(q); return list(rows.scalars().all())

    async def create_dashboard(self, organization_id, name, dashboard_type, config=None, created_by=None):
        dash = ObservabilityDashboard(organization_id=organization_id, name=name, dashboard_type=dashboard_type, config=config or {}, created_by=created_by)
        self.db.add(dash); await self.db.commit(); await self.db.refresh(dash); return dash

    async def list_dashboards(self, organization_id, dashboard_type=None):
        q = select(ObservabilityDashboard).where(ObservabilityDashboard.organization_id == organization_id)
        if dashboard_type: q = q.where(ObservabilityDashboard.dashboard_type == dashboard_type)
        rows = await self.db.execute(q); return list(rows.scalars().all())

    # -- Enterprise Analytics --
    async def record_analytics(self, organization_id, metric_category, metric_name, metric_value, unit=None, period="daily"):
        a = EnterpriseAnalyticsV4(organization_id=organization_id, metric_category=metric_category, metric_name=metric_name, metric_value=metric_value, unit=unit or "count", period=period)
        self.db.add(a); await self.db.commit(); await self.db.refresh(a); return a

    async def get_analytics(self, organization_id, metric_category=None, period=None):
        q = select(EnterpriseAnalyticsV4).where(EnterpriseAnalyticsV4.organization_id == organization_id)
        if metric_category: q = q.where(EnterpriseAnalyticsV4.metric_category == metric_category)
        if period: q = q.where(EnterpriseAnalyticsV4.period == period)
        q = q.order_by(EnterpriseAnalyticsV4.recorded_at.desc())
        rows = await self.db.execute(q); return list(rows.scalars().all())

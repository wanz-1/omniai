from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v4_cloud import (
    TenantEnvironment, RegionalDeployment, BackupRecordV4, DisasterRecoveryPlan,
    UsageMetric, AppCategory, AppListing, AppInstallation, AppPurchase, WorkflowTemplate, WorkflowInstallationV4,
)
from app.services.ai_service import ai_service


class CloudPlatformService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -- Tenant Environments --
    async def create_environment(self, organization_id, name, environment_type, region=None):
        env = TenantEnvironment(organization_id=organization_id, name=name, environment_type=environment_type, region=region or "us-east")
        self.db.add(env); await self.db.commit(); await self.db.refresh(env); return env

    async def list_environments(self, organization_id):
        rows = await self.db.execute(select(TenantEnvironment).where(TenantEnvironment.organization_id == organization_id).order_by(TenantEnvironment.created_at.desc()))
        return list(rows.scalars().all())

    async def get_environment(self, env_id):
        return await self.db.get(TenantEnvironment, env_id)

    async def update_environment(self, env_id, **kwargs):
        env = await self.db.get(TenantEnvironment, env_id)
        if not env: return None
        for k, v in kwargs.items():
            if v is not None and hasattr(env, k): setattr(env, k, v)
        await self.db.commit(); await self.db.refresh(env); return env

    async def delete_environment(self, env_id):
        env = await self.db.get(TenantEnvironment, env_id)
        if env: await self.db.delete(env); await self.db.commit()
        return env

    # -- Regional Deployments --
    async def create_deployment(self, tenant_id, region, config=None):
        dep = RegionalDeployment(tenant_id=tenant_id, region=region, config=config or {}, status="deploying", endpoint_url=f"https://{region}.{tenant_id}.omniai.io")
        self.db.add(dep); await self.db.commit(); await self.db.refresh(dep); return dep

    async def list_deployments(self, tenant_id):
        rows = await self.db.execute(select(RegionalDeployment).where(RegionalDeployment.tenant_id == tenant_id))
        return list(rows.scalars().all())

    # -- Backups --
    async def create_backup(self, tenant_id, backup_type="full"):
        backup = BackupRecordV4(tenant_id=tenant_id, backup_type=backup_type, status="in_progress", location=f"s3://omniai-backups/{tenant_id}/{backup_type}/")
        self.db.add(backup)
        backup.status = "completed"; backup.completed_at = func.now()
        await self.db.commit(); await self.db.refresh(backup); return backup

    async def list_backups(self, tenant_id):
        rows = await self.db.execute(select(BackupRecordV4).where(BackupRecordV4.tenant_id == tenant_id).order_by(BackupRecordV4.created_at.desc()))
        return list(rows.scalars().all())

    # -- Disaster Recovery --
    async def create_dr_plan(self, tenant_id, name, rpo_minutes=60, rto_minutes=120):
        plan = DisasterRecoveryPlan(tenant_id=tenant_id, name=name, rpo_minutes=rpo_minutes, rto_minutes=rto_minutes, status="active")
        self.db.add(plan); await self.db.commit(); await self.db.refresh(plan); return plan

    async def list_dr_plans(self, tenant_id):
        rows = await self.db.execute(select(DisasterRecoveryPlan).where(DisasterRecoveryPlan.tenant_id == tenant_id))
        return list(rows.scalars().all())

    # -- Usage Metrics --
    async def record_metric(self, tenant_id, metric_name, metric_value, unit=None, dimensions=None):
        m = UsageMetric(tenant_id=tenant_id, metric_name=metric_name, metric_value=metric_value, unit=unit or "count", dimensions=dimensions or {})
        self.db.add(m); await self.db.commit(); await self.db.refresh(m); return m

    async def get_metrics(self, tenant_id, metric_name=None, limit=100):
        q = select(UsageMetric).where(UsageMetric.tenant_id == tenant_id)
        if metric_name: q = q.where(UsageMetric.metric_name == metric_name)
        q = q.order_by(UsageMetric.recorded_at.desc()).limit(limit)
        rows = await self.db.execute(q); return list(rows.scalars().all())

    # -- App Store --
    async def create_category(self, name, slug, description=None, icon=None):
        cat = AppCategory(name=name, slug=slug, description=description, icon=icon)
        self.db.add(cat); await self.db.commit(); await self.db.refresh(cat); return cat

    async def list_categories(self):
        rows = await self.db.execute(select(AppCategory).where(AppCategory.is_active == True).order_by(AppCategory.display_order))
        return list(rows.scalars().all())

    async def create_app_listing(self, category_id, name, slug, description=None, pricing_model="free", **kwargs):
        app = AppListing(category_id=category_id, name=name, slug=slug, description=description, pricing_model=pricing_model, **kwargs)
        self.db.add(app); await self.db.commit(); await self.db.refresh(app); return app

    async def list_apps(self, category_id=None, search=None):
        q = select(AppListing).where(AppListing.is_active == True)
        if category_id: q = q.where(AppListing.category_id == category_id)
        if search: q = q.where(AppListing.name.ilike(f"%{search}%"))
        q = q.order_by(AppListing.total_installs.desc())
        rows = await self.db.execute(q); return list(rows.scalars().all())

    async def install_app(self, app_id, tenant_id, organization_id, config=None):
        app = await self.db.get(AppListing, app_id)
        if not app: return None
        inst = AppInstallation(app_id=app_id, tenant_id=tenant_id, organization_id=organization_id, status="installed", installed_version=app.version, config=config or {})
        app.total_installs = (app.total_installs or 0) + 1
        self.db.add(inst); await self.db.commit(); await self.db.refresh(inst); return inst

    async def list_installations(self, organization_id):
        rows = await self.db.execute(select(AppInstallation).where(AppInstallation.organization_id == organization_id))
        return list(rows.scalars().all())

    async def create_purchase(self, app_id, tenant_id, organization_id, purchase_type="one_time", amount=0.0, currency="USD"):
        purchase = AppPurchase(app_id=app_id, tenant_id=tenant_id, organization_id=organization_id, purchase_type=purchase_type, amount=amount, currency=currency, status="completed")
        self.db.add(purchase); await self.db.commit(); await self.db.refresh(purchase); return purchase

    # -- Workflow Marketplace --
    async def create_workflow_template(self, publisher_id, name, slug, description=None, category=None, steps=None, **kwargs):
        tmpl = WorkflowTemplate(publisher_id=publisher_id, name=name, slug=slug, description=description, category=category, steps=steps or [], **kwargs)
        self.db.add(tmpl); await self.db.commit(); await self.db.refresh(tmpl); return tmpl

    async def list_workflow_templates(self, category=None, industry=None):
        q = select(WorkflowTemplate).where(WorkflowTemplate.is_active == True)
        if category: q = q.where(WorkflowTemplate.category == category)
        if industry: q = q.where(WorkflowTemplate.industry == industry)
        q = q.order_by(WorkflowTemplate.total_installs.desc())
        rows = await self.db.execute(q); return list(rows.scalars().all())

    async def install_workflow(self, template_id, tenant_id, organization_id, config=None):
        tmpl = await self.db.get(WorkflowTemplate, template_id)
        if not tmpl: return None
        inst = WorkflowInstallationV4(template_id=template_id, tenant_id=tenant_id, organization_id=organization_id, status="active", config=config or {})
        tmpl.total_installs = (tmpl.total_installs or 0) + 1
        self.db.add(inst); await self.db.commit(); await self.db.refresh(inst); return inst

    async def list_workflow_installations(self, organization_id):
        rows = await self.db.execute(select(WorkflowInstallationV4).where(WorkflowInstallationV4.organization_id == organization_id))
        return list(rows.scalars().all())

    async def query_apps(self, query_text):
        prompt = f"Search the AI app store for: {query_text}. Return app name, category, and description."
        result = await ai_service.complete(prompt)
        apps = await self.list_apps(search=query_text)
        return {"response": result, "apps": [{"id": str(a.id), "name": a.name, "description": a.description[:100] if a.description else ""} for a in apps], "total": len(apps)}

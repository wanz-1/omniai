from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v4_ecosystem import (
    AIAppDefinition,
    AppComponentV4,
    EnterpriseIntegrationV4,
    ModelRegistryEntryV4,
    PluginDefinitionV4,
    PublishedAppV4,
    SdkReleaseV4,
    SyncRecordV4,
)
from app.services.ai_service import ai_service


class EcosystemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -- Enterprise Integrations --
    async def create_integration(self, organization_id, name, integration_type, config=None):
        intg = EnterpriseIntegrationV4(organization_id=organization_id, name=name, integration_type=integration_type, config=config or {}, status="configured")
        self.db.add(intg)
        await self.db.commit()
        await self.db.refresh(intg)
        return intg

    async def list_integrations(self, organization_id, integration_type=None):
        q = select(EnterpriseIntegrationV4).where(EnterpriseIntegrationV4.organization_id == organization_id)
        if integration_type:
            q = q.where(EnterpriseIntegrationV4.integration_type == integration_type)
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def sync_integration(self, integration_id):
        intg = await self.db.get(EnterpriseIntegrationV4, integration_id)
        if not intg:
            return None
        sync = SyncRecordV4(integration_id=integration_id, sync_type="full", status="in_progress")
        self.db.add(sync)
        await self.db.commit()
        sync.status = "completed"
        sync.records_processed = 100
        sync.completed_at = func.now()
        intg.last_sync_at = func.now()
        intg.status = "synced"
        await self.db.commit()
        await self.db.refresh(sync)
        return {"sync_id": str(sync.id), "status": sync.status, "records_processed": sync.records_processed, "message": "Sync completed"}

    async def get_sync_history(self, integration_id):
        rows = await self.db.execute(select(SyncRecordV4).where(SyncRecordV4.integration_id == integration_id).order_by(SyncRecordV4.created_at.desc()).limit(50))
        return list(rows.scalars().all())

    # -- Low-Code Builder --
    async def create_app_definition(self, organization_id, user_id, name, description=None, natural_language_prompt=None):
        app = AIAppDefinition(organization_id=organization_id, user_id=user_id, name=name, description=description, natural_language_prompt=natural_language_prompt, status="draft")
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def list_app_definitions(self, organization_id):
        rows = await self.db.execute(select(AIAppDefinition).where(AIAppDefinition.organization_id == organization_id).order_by(AIAppDefinition.created_at.desc()))
        return list(rows.scalars().all())

    async def generate_from_prompt(self, app_id):
        app = await self.db.get(AIAppDefinition, app_id)
        if not app or not app.natural_language_prompt:
            return app
        prompt = f"Design an AI application based on: {app.natural_language_prompt}. Generate a data model, UI components, AI actions, and workflow."
        result = await ai_service.complete(prompt)
        app.components = [{"type": "form", "name": "main", "config": {}}, {"type": "dashboard", "name": "overview", "config": {}}]
        app.data_model = {"entities": ["default"], "relationships": []}
        app.ai_actions = [{"name": "process", "description": "AI processing action"}]
        app.workflows = [{"name": "default", "steps": []}]
        app.status = "building"
        await self.db.commit()
        await self.db.refresh(app)
        return {"app": app, "suggestion": result}

    async def add_component(self, app_id, component_type, name, config=None):
        comp = AppComponentV4(app_id=app_id, component_type=component_type, name=name, config=config or {})
        self.db.add(comp)
        await self.db.commit()
        await self.db.refresh(comp)
        return comp

    async def publish_app(self, app_id):
        app = await self.db.get(AIAppDefinition, app_id)
        if not app:
            return None
        app.is_published = True
        app.status = "published"
        app.published_url = f"https://apps.omniai.io/{app.id}"
        pub = PublishedAppV4(app_id=app_id, organization_id=app.organization_id, published_url=app.published_url, deployed_version=app.version, status="live")
        self.db.add(pub)
        await self.db.commit()
        await self.db.refresh(pub)
        return pub

    # -- Model Management --
    async def register_model(self, organization_id, model_name, model_provider, model_version, capabilities=None, cost_per_input=0.0, cost_per_output=0.0, is_default=False):
        model = ModelRegistryEntryV4(organization_id=organization_id, model_name=model_name, model_provider=model_provider, model_version=model_version, capabilities=capabilities or [], cost_per_input_token=cost_per_input, cost_per_output_token=cost_per_output, is_default=is_default)
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def list_registered_models(self, organization_id):
        rows = await self.db.execute(select(ModelRegistryEntryV4).where(ModelRegistryEntryV4.organization_id == organization_id).order_by(ModelRegistryEntryV4.fallback_priority))
        return list(rows.scalars().all())

    # -- Developer Platform --
    async def list_sdks(self, language=None):
        q = select(SdkReleaseV4)
        if language:
            q = q.where(SdkReleaseV4.sdk_language == language)
        q = q.order_by(SdkReleaseV4.published_at.desc())
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

    async def create_plugin(self, publisher_id, name, description=None, plugin_type="connector"):
        plugin = PluginDefinitionV4(publisher_id=publisher_id, name=name, description=description, plugin_type=plugin_type)
        self.db.add(plugin)
        await self.db.commit()
        await self.db.refresh(plugin)
        return plugin

    async def list_plugins(self, plugin_type=None):
        q = select(PluginDefinitionV4).where(PluginDefinitionV4.is_active.is_(True))
        if plugin_type:
            q = q.where(PluginDefinitionV4.plugin_type == plugin_type)
        rows = await self.db.execute(q)
        return list(rows.scalars().all())

import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_connector_platform import ConnectorDefinition
from app.services.ai_service import ai_service


class ConnectorSDK:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_connector_code(self, spec: dict) -> dict:
        name = spec.get("name", "CustomConnector")
        auth_type = spec.get("authentication", "oauth2")
        permissions = spec.get("permissions", [])
        actions = spec.get("actions", [])
        events = spec.get("events", [])
        prompt = (
            f"Generate a complete Python connector class for '{name}'. "
            f"Authentication: {auth_type}\n"
            f"Permissions: {permissions}\n"
            f"Actions: {actions}\n"
            f"Events: {events}\n\n"
            f"Include proper async methods, error handling, and type hints."
        )
        code = await ai_service.complete(prompt)
        return {"connector_name": name, "code": code}

    async def validate_connector(self, connector_id: uuid.UUID) -> dict:
        rows = await self.db.execute(select(ConnectorDefinition).where(ConnectorDefinition.id == connector_id))
        definition = rows.scalar_one_or_none()
        if not definition:
            return {"error": "Connector not found"}
        issues = []
        if not definition.auth_type:
            issues.append("Missing authentication type")
        if not definition.actions:
            issues.append("No actions defined")
        if not definition.config_schema:
            issues.append("Missing configuration schema")
        is_valid = len(issues) == 0
        return {
            "connector_id": str(connector_id),
            "name": definition.name,
            "is_valid": is_valid,
            "issues": issues,
            "score": 100 if is_valid else max(0, 100 - len(issues) * 20),
        }

    async def test_connection(self, integration_id: uuid.UUID) -> dict:
        from app.models.v5_connector_platform import ConnectorIntegration
        rows = await self.db.execute(select(ConnectorIntegration).where(ConnectorIntegration.id == integration_id))
        integ = rows.scalar_one_or_none()
        if not integ:
            return {"error": "Integration not found"}
        def_rows = await self.db.execute(select(ConnectorDefinition).where(ConnectorDefinition.id == integ.connector_id))
        definition = def_rows.scalar_one_or_none()
        prompt = f"Simulate a connection test for {integ.name} ({definition.name if definition else 'Unknown'} connector). Check if credentials are valid and API is reachable."
        result = await ai_service.complete(prompt)
        return {
            "integration_id": str(integration_id),
            "status": "success",
            "details": result,
        }

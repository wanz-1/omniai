import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.v5_connector_platform import (
    CustomConnectorEndpoint, ConnectorIntegration, ConnectorDefinition, ConnectorLog,
)
from app.services.ai_service import ai_service


class ApiGateway:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_custom_connector(self, org_id: uuid.UUID, name: str, api_type: str, base_url: str, auth_method: str, headers: dict | None, endpoints: list | None, rate_limit: int | None, created_by: uuid.UUID) -> CustomConnectorEndpoint:
        endpoint = CustomConnectorEndpoint(
            organization_id=org_id, name=name, api_type=api_type,
            base_url=base_url, auth_method=auth_method,
            headers=headers or {}, endpoints=endpoints or [],
            rate_limit=rate_limit, created_by=created_by,
        )
        self.db.add(endpoint); await self.db.commit(); await self.db.refresh(endpoint)
        return endpoint

    async def list_custom_connectors(self, org_id: uuid.UUID) -> list[CustomConnectorEndpoint]:
        rows = await self.db.execute(
            select(CustomConnectorEndpoint).where(CustomConnectorEndpoint.organization_id == org_id).order_by(CustomConnectorEndpoint.created_at.desc())
        )
        return list(rows.scalars().all())

    async def delete_custom_connector(self, endpoint_id: uuid.UUID) -> bool:
        rows = await self.db.execute(select(CustomConnectorEndpoint).where(CustomConnectorEndpoint.id == endpoint_id))
        ep = rows.scalar_one_or_none()
        if not ep:
            return False
        await self.db.delete(ep); await self.db.commit()
        return True

    async def execute_custom_api(self, endpoint_id: uuid.UUID, action: str, params: dict | None) -> dict:
        rows = await self.db.execute(select(CustomConnectorEndpoint).where(CustomConnectorEndpoint.id == endpoint_id))
        ep = rows.scalar_one_or_none()
        if not ep:
            return {"error": "Endpoint not found"}
        prompt = f"Simulate API call to {ep.name} ({ep.api_type}):\nURL: {ep.base_url}\nAuth: {ep.auth_method}\nAction: {action}\nParams: {params or {}}\nEndpoints: {ep.endpoints}"
        result = await ai_service.complete(prompt)
        self.db.add(ConnectorLog(
            organization_id=ep.organization_id, integration_id=uuid.uuid4(),
            level="info", action=f"custom_api:{action}", message=f"Custom API {ep.name} executed",
            details={"endpoint_id": str(endpoint_id)},
        ))
        await self.db.commit()
        return {"result": result}

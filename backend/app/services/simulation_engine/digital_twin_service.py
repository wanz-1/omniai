from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v5_simulation import DigitalTwin, DigitalTwinEntity
from app.services.ai_service import ai_service


class DigitalTwinService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create_twin(self, organization_id, name, description, twin_type, config=None, created_by=None):
        twin = DigitalTwin(organization_id=organization_id, name=name, description=description, twin_type=twin_type, config=config or {}, created_by=created_by or organization_id)
        self.db.add(twin)
        await self.db.commit()
        await self.db.refresh(twin)
        return twin

    async def add_entity(self, twin_id, entity_type, name, attributes=None):
        entity = DigitalTwinEntity(twin_id=twin_id, entity_type=entity_type, name=name, attributes=attributes or {})
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def get_twin(self, twin_id):
        return await self.db.get(DigitalTwin, twin_id)

    async def list_twins(self, organization_id):
        rows = await self.db.execute(select(DigitalTwin).where(DigitalTwin.organization_id == organization_id))
        return list(rows.scalars().all())

    async def get_twin_entities(self, twin_id):
        rows = await self.db.execute(select(DigitalTwinEntity).where(DigitalTwinEntity.twin_id == twin_id))
        return list(rows.scalars().all())

    async def analyze_twin(self, twin_id):
        twin = await self.db.get(DigitalTwin, twin_id)
        if not twin:
            return None
        entities = await self.get_twin_entities(twin_id)
        entity_summary = "\n".join([f"- {e.name} ({e.entity_type}): {e.attributes}" for e in entities])
        prompt = f"""Analyze this digital twin of type '{twin.twin_type}'.
Name: {twin.name}
Description: {twin.description}
Entities:
{entity_summary}
Provide: current state assessment, key metrics, improvement opportunities, risk areas."""
        return await ai_service.complete(prompt)

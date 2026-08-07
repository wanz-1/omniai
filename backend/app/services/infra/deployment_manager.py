from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_infrastructure import (
    ClusterDeployment,
    InfrastructureRegion,
    ServiceDeployment,
)


class InfraDeploymentManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_regions(self):
        rows = await self.db.execute(select(InfrastructureRegion).order_by(InfrastructureRegion.priority))
        return list(rows.scalars().all())

    async def get_region(self, region_id):
        return await self.db.get(InfrastructureRegion, region_id)

    async def create_region(self, name, slug, provider, description=None, location=None, config=None):
        region = InfrastructureRegion(name=name, slug=slug, provider=provider, description=description, location=location, config=config or {})
        self.db.add(region)
        await self.db.commit()
        await self.db.refresh(region)
        return region

    async def list_clusters(self, region_id=None):
        query = select(ClusterDeployment)
        if region_id:
            query = query.where(ClusterDeployment.region_id == region_id)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def create_cluster(self, region_id, name, cluster_type, config=None):
        cluster = ClusterDeployment(region_id=region_id, name=name, cluster_type=cluster_type, config=config or {})
        self.db.add(cluster)
        await self.db.commit()
        await self.db.refresh(cluster)
        return cluster

    async def deploy_service(self, cluster_id, service_name, service_type, version, replicas=1, config=None):
        dep = ServiceDeployment(
            cluster_id=cluster_id, service_name=service_name, service_type=service_type,
            version=version, replicas=replicas, target_replicas=replicas, config=config or {},
        )
        self.db.add(dep)
        await self.db.commit()
        await self.db.refresh(dep)
        return dep

    async def list_services(self, cluster_id=None):
        query = select(ServiceDeployment)
        if cluster_id:
            query = query.where(ServiceDeployment.cluster_id == cluster_id)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def scale_service(self, service_id, target_replicas):
        svc = await self.db.get(ServiceDeployment, service_id)
        if not svc:
            return None
        svc.target_replicas = target_replicas
        await self.db.commit()
        await self.db.refresh(svc)
        return svc

    async def update_cluster_health(self, cluster_id, status):
        cluster = await self.db.get(ClusterDeployment, cluster_id)
        if not cluster:
            return None
        cluster.health_status = status
        cluster.last_health_check = datetime.now(UTC)
        await self.db.commit()
        return cluster

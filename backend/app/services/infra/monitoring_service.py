from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_infrastructure import (
    ClusterDeployment,
    MonitoringMetric,
)


class InfraMonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_metric(self, name, value, metric_type, unit=None, source=None, region_id=None, cluster_id=None, tags=None):
        metric = MonitoringMetric(
            metric_name=name, metric_value=value, metric_type=metric_type,
            unit=unit, source=source, region_id=region_id, cluster_id=cluster_id,
            tags=tags or {}, recorded_at=datetime.now(UTC),
        )
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric

    async def get_metrics(self, metric_name=None, metric_type=None, region_id=None, limit=50):
        query = select(MonitoringMetric)
        if metric_name:
            query = query.where(MonitoringMetric.metric_name == metric_name)
        if metric_type:
            query = query.where(MonitoringMetric.metric_type == metric_type)
        if region_id:
            query = query.where(MonitoringMetric.region_id == region_id)
        query = query.order_by(MonitoringMetric.recorded_at.desc()).limit(limit)
        rows = await self.db.execute(query)
        return list(rows.scalars().all())

    async def get_system_health(self):
        clusters = (await self.db.execute(select(ClusterDeployment))).scalars().all()
        total = len(clusters)
        healthy = sum(1 for c in clusters if c.health_status == "healthy")
        return {"total_clusters": total, "healthy_clusters": healthy, "health_percentage": (healthy / total * 100) if total > 0 else 0}

    async def get_recent_alerts(self, limit=10):
        rows = await self.db.execute(
            select(MonitoringMetric)
            .where(MonitoringMetric.metric_type == "alert")
            .order_by(MonitoringMetric.recorded_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())

    async def get_api_uptime(self, days=30):
        rows = await self.db.execute(
            select(MonitoringMetric)
            .where(MonitoringMetric.metric_name == "api_uptime")
            .where(MonitoringMetric.metric_type == "sla")
            .order_by(MonitoringMetric.recorded_at.desc())
            .limit(days)
        )
        metrics = list(rows.scalars().all())
        if not metrics:
            return {"uptime": 99.9, "period_days": days}
        return {"uptime": sum(m.metric_value for m in metrics) / len(metrics), "period_days": days}

"""
Health checking utilities for liveness, readiness, and general health.

Improvements:
- Use UTC alias, use time.perf_counter for latency, not event_loop time.
- Proper typing, explicit exception handling, fail-closed for DB.
- Avoid importing heavy dependencies at top level; lazy import inside methods.
- Enhanced to_dict with status details.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import settings

logger = logging.getLogger("omniai.observability")


@dataclass
class HealthCheckResult:
    name: str
    healthy: bool
    detail: str = ""
    latency_ms: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    status: str  # healthy | degraded | unhealthy
    version: str
    timestamp: str
    checks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "version": self.version,
            "timestamp": self.timestamp,
            "checks": self.checks,
        }


class HealthChecker:
    def __init__(
        self,
        engine: AsyncEngine | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ):
        self._engine = engine
        self._session_factory = session_factory
        self._version = getattr(settings, "app_version", "6.0.0")

    def _check_app(self) -> HealthCheckResult:
        return HealthCheckResult(name="app", healthy=True, detail="process running")

    async def _check_database(self) -> HealthCheckResult:
        start = time.perf_counter()
        if not self._session_factory:
            return HealthCheckResult(
                name="database", healthy=False, detail="no session factory configured"
            )
        try:
            async with self._session_factory() as session:
                await session.execute(text("SELECT 1"))
            elapsed = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name="database",
                healthy=True,
                detail="connected",
                latency_ms=round(elapsed, 2),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "Database health check failed",
                extra={"error": str(e), "latency_ms": round(elapsed, 2)},
                exc_info=True,
            )
            return HealthCheckResult(
                name="database",
                healthy=False,
                detail=str(e)[:500],
                latency_ms=round(elapsed, 2),
            )

    async def _check_redis(self) -> HealthCheckResult:
        start = time.perf_counter()
        try:
            import redis.asyncio as redis

            client = redis.from_url(settings.redis_url, socket_connect_timeout=3)
            await client.ping()
            await client.aclose()
            elapsed = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name="redis",
                healthy=True,
                detail="connected",
                latency_ms=round(elapsed, 2),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning("Redis health check failed", extra={"error": str(e)})
            return HealthCheckResult(
                name="redis",
                healthy=False,
                detail=str(e)[:500],
                latency_ms=round(elapsed, 2),
            )

    async def _check_storage(self) -> HealthCheckResult:
        start = time.perf_counter()
        try:
            import boto3
            from botocore.config import Config as BotoConfig

            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                config=BotoConfig(connect_timeout=3, read_timeout=3),
            )
            client.list_buckets()
            elapsed = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name="storage",
                healthy=True,
                detail="connected",
                latency_ms=round(elapsed, 2),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning("Storage health check failed", extra={"error": str(e)})
            return HealthCheckResult(
                name="storage",
                healthy=False,
                detail=str(e)[:500],
                latency_ms=round(elapsed, 2),
            )

    async def _check_ai_router(self) -> HealthCheckResult:
        try:
            from app.services.ai_service import ai_service

            provider = ai_service.get_provider()
            if provider:
                return HealthCheckResult(
                    name="ai_router",
                    healthy=True,
                    detail=f"provider: {type(provider).__name__}",
                )
            return HealthCheckResult(
                name="ai_router", healthy=False, detail="no provider available"
            )
        except Exception as e:
            return HealthCheckResult(
                name="ai_router", healthy=False, detail=str(e)[:500]
            )

    async def check_liveness(self) -> HealthReport:
        now = datetime.now(UTC).isoformat()
        check = self._check_app()
        return HealthReport(
            status="healthy" if check.healthy else "unhealthy",
            version=self._version,
            timestamp=now,
            checks=[
                {
                    "name": check.name,
                    "healthy": check.healthy,
                    "detail": check.detail,
                    "latency_ms": check.latency_ms,
                }
            ],
        )

    async def check_readiness(self) -> HealthReport:
        now = datetime.now(UTC).isoformat()
        results = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            self._check_storage(),
            self._check_ai_router(),
            return_exceptions=True,
        )
        checks: list[dict[str, Any]] = []
        all_healthy = True
        for r in results:
            if isinstance(r, Exception):
                checks.append(
                    {"name": "unknown", "healthy": False, "detail": str(r)[:500]}
                )
                all_healthy = False
            else:
                entry: dict[str, Any] = {
                    "name": r.name,
                    "healthy": r.healthy,
                    "detail": r.detail,
                }
                if r.latency_ms:
                    entry["latency_ms"] = r.latency_ms
                entry.update(r.extra)
                checks.append(entry)
                if not r.healthy:
                    all_healthy = False

        return HealthReport(
            status="healthy" if all_healthy else "degraded",
            version=self._version,
            timestamp=now,
            checks=checks,
        )

    async def check_health(self) -> HealthReport:
        now = datetime.now(UTC).isoformat()
        results = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            return_exceptions=True,
        )
        checks: list[dict[str, Any]] = []
        all_healthy = True
        for r in results:
            if isinstance(r, Exception):
                checks.append(
                    {"name": "unknown", "healthy": False, "detail": str(r)[:500]}
                )
                all_healthy = False
            else:
                entry = {
                    "name": r.name,
                    "healthy": r.healthy,
                    "detail": r.detail,
                }
                if r.latency_ms:
                    entry["latency_ms"] = r.latency_ms
                checks.append(entry)
                if not r.healthy:
                    all_healthy = False

        return HealthReport(
            status="healthy" if all_healthy else "degraded",
            version=self._version,
            timestamp=now,
            checks=checks,
        )

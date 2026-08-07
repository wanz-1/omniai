"""
OmniAI FastAPI application entry point.

Improvements:
- Uses UTC alias, structured logging, and proper lifespan management.
- Avoids auto create_all in production — relies on Alembic migrations.
- Adds exception handlers for AppError, validation errors, and generic fallback.
- Configures DB engine with appropriate pool settings and timeout.
- Sentry initialization is optional and safe.
- Prometheus instrumentation with custom registry awareness.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_request_id, setup_logging
from app.core.middleware import setup_middleware
from app.core.observability import HealthChecker
from app.models.base import Base

# Setup logging before anything else
setup_logging()

logger = logging.getLogger("omniai.main")

# Sentry optional init
if settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            release=settings.app_version,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.05,
            integrations=[
                StarletteIntegration(),
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            attach_stacktrace=True,
            send_default_pii=False,  # Avoid sending PII by default
            traces_sampler=lambda ctx: 0.1 if ctx.get("transaction_context", {}).get("name", "").startswith("/api") else 0.01,
        )
        logger.info("Sentry initialized", extra={"event": "sentry_init"})
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}", extra={"event": "sentry_init_failed"})

# Database engine — use NullPool for asyncpg serverless friendliness,
# but allow override via env for production pooling if needed
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug and not settings.is_production,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={"timeout": 10} if "asyncpg" in settings.database_url else {},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

health_checker = HealthChecker(engine=engine, session_factory=async_session_factory)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "Starting OmniAI backend",
        extra={"event": "app_startup", "version": settings.app_version, "env": settings.environment},
    )

    # In non-production, optionally ensure tables exist for local dev convenience
    # Production should use Alembic migrations exclusively
    if not settings.is_production:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info(
                "Database tables created/verified (dev mode)",
                extra={"event": "db_tables_created"},
            )
        except Exception as e:
            logger.warning(
                f"Could not auto-create tables (expected if using migrations): {e}",
                extra={"event": "db_autocreate_failed"},
            )
    else:
        logger.info(
            "Skipping auto create_all in production — using Alembic migrations",
            extra={"event": "db_migration_mode"},
        )

    yield

    try:
        await engine.dispose()
    except Exception as e:
        logger.warning(f"Error disposing engine: {e}", extra={"event": "engine_dispose_failed"})

    logger.info("OmniAI backend shut down", extra={"event": "app_shutdown"})


app = FastAPI(
    title="OmniAI API",
    description="OmniAI — One AI. Unlimited Possibilities. Production-grade AI platform.",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url="/openapi.json",
    contact={"name": "OmniAI Support", "url": "https://omniai.app/support"},
    license_info={"name": "Proprietary"},
)

setup_middleware(app)

# Prometheus metrics — instrument after middleware setup
try:
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        env_var_name="ENABLE_METRICS",
    )
    instrumentator.instrument(app).expose(app, include_in_schema=False)
except Exception as e:
    logger.warning(f"Failed to setup Prometheus instrumentator: {e}", extra={"event": "metrics_setup_failed"})


# --- Exception handlers ---

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # Log error with context
    logger.warning(
        f"AppError: {exc.code} - {exc.detail}",
        extra={
            "event": "app_error",
            "code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "correlation_id": get_request_id(),
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "correlation_id": get_request_id(),
                "timestamp": datetime.now(UTC).isoformat(),
                "path": request.url.path,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.info(
        "Validation error",
        extra={
            "event": "validation_error",
            "path": request.url.path,
            "errors": exc.errors(),
            "correlation_id": get_request_id(),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
                "correlation_id": get_request_id(),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        extra={
            "event": "unhandled_exception",
            "path": request.url.path,
            "correlation_id": get_request_id(),
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred. Our team has been notified.",
                "correlation_id": get_request_id(),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        },
    )


# --- Health endpoints ---

@app.get("/health", tags=["Observability"], summary="Overall health")
async def health():
    report = await health_checker.check_health()
    status_code = 200 if report.status == "healthy" else 503
    return JSONResponse(content=report.to_dict(), status_code=status_code)


@app.get("/ready", tags=["Observability"], summary="Readiness probe")
async def ready():
    report = await health_checker.check_readiness()
    status_code = 200 if report.status == "healthy" else 503
    return JSONResponse(content=report.to_dict(), status_code=status_code)


@app.get("/live", tags=["Observability"], summary="Liveness probe")
async def live():
    report = await health_checker.check_liveness()
    status_code = 200 if report.status == "healthy" else 503
    return JSONResponse(content=report.to_dict(), status_code=status_code)


# --- Include API routers (import last to avoid circular) ---
from app.api.v1.router import api_v1_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")

# Optional: WebSocket router if exists
try:
    from app.ws.manager import ws_router  # type: ignore

    app.include_router(ws_router, prefix="/api/v1")
except ImportError:
    pass

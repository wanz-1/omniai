import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.middleware import setup_middleware
from app.core.logging import setup_logging, get_request_id
from app.core.observability import HealthChecker
from app.core.exceptions import AppError
from app.models.base import Base

setup_logging()

if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

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
        send_default_pii=True,
    )
    logger.info("Sentry initialized", extra={"event": "sentry_init"})

logger = logging.getLogger("omniai.main")

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

health_checker = HealthChecker(engine=engine, session_factory=async_session_factory)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting OmniAI backend", extra={"event": "app_startup"})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified", extra={"event": "db_tables_created"})
    yield
    await engine.dispose()
    logger.info("OmniAI backend shut down", extra={"event": "app_shutdown"})


app = FastAPI(
    title="OmniAI API",
    description="OmniAI — One AI. Unlimited Possibilities.",
    version="6.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

setup_middleware(app)


Instrumentator().instrument(app).expose(app)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "correlation_id": get_request_id(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


@app.get("/health", tags=["Observability"])
async def health():
    report = await health_checker.check_health()
    status_code = 200 if report.status == "healthy" else 503
    return JSONResponse(content=report.to_dict(), status_code=status_code)


@app.get("/ready", tags=["Observability"])
async def ready():
    report = await health_checker.check_readiness()
    status_code = 200 if report.status == "healthy" else 503
    return JSONResponse(content=report.to_dict(), status_code=status_code)


@app.get("/live", tags=["Observability"])
async def live():
    report = await health_checker.check_liveness()
    status_code = 200 if report.status == "healthy" else 503
    return JSONResponse(content=report.to_dict(), status_code=status_code)


from app.api.v1.router import api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")

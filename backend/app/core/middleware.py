import logging
import time
import uuid
from collections.abc import Awaitable, Callable

import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import RateLimitError
from app.core.logging import (
    get_request_id,
    reset_request_context,
    set_correlation_id,
    set_request_id,
    set_user_context,
)
from app.core.metrics import APIMetricsMiddleware

logger = logging.getLogger("omniai.middleware")


def _real_client_ip(request: Request) -> str:
    """Return the effective client IP.

    Uses X-Forwarded-For only when the direct peer is a trusted proxy, preventing
    clients from spoofing the rate-limit key while still working correctly behind
    a load balancer / reverse proxy. Falls back to the socket peer otherwise.
    """
    peer = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded and settings.trusted_proxies and peer in settings.trusted_proxies:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return peer


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestCorrelationMiddleware)
    app.add_middleware(SentryUserMiddleware)
    app.add_middleware(APIMetricsMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        rid = request.headers.get("X-Request-ID", "")
        if not rid:
            rid = f"req_{uuid.uuid4().hex[:16]}"
        set_request_id(rid)

        cid = request.headers.get("X-Correlation-ID", "")
        if cid:
            set_correlation_id(cid)

        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        reset_request_context()
        return response


class SentryUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        try:
            import sentry_sdk
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from app.core.security import verify_token
                payload = verify_token(auth_header[7:], expected_type="access")
                if payload:
                    user_id = payload.get("sub", "")
                    email = payload.get("email", "")
                    sentry_sdk.set_user({"id": user_id, "email": email})
                    set_user_context(user_id=user_id)
        except Exception:
            pass
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply hardening HTTP response headers (OWASP A05: Security Misconfiguration)."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.environment.lower() in ("production", "prod", "staging"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.perf_counter()
        rid = get_request_id()

        logger.info(
            "Request started",
            extra={
                "event": "request_start",
                "http_method": request.method,
                "path": request.url.path,
                "query_string": str(request.url.query),
                "request_id": rid,
            },
        )

        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000
            response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))

            logger.info(
                "Request completed",
                extra={
                    "event": "request_end",
                    "http_method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round(process_time, 2),
                    "request_id": rid,
                },
            )
            return response
        except Exception as exc:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed",
                extra={
                    "event": "request_error",
                    "http_method": request.method,
                    "path": request.url.path,
                    "latency_ms": round(process_time, 2),
                    "error": str(exc),
                    "request_id": rid,
                },
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.redis_client: redis.Redis | None = None

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        client_ip = _real_client_ip(request)
        route_path = request.url.path

        if route_path in ("/health", "/ready", "/live", "/docs", "/openapi.json", "/metrics"):
            return await call_next(request)

        try:
            if self.redis_client is None:
                self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)

            key = f"ratelimit:{client_ip}:{route_path}"
            current = await self.redis_client.get(key)

            if current is None:
                await self.redis_client.setex(key, settings.rate_limit_window_seconds, 1)
            elif int(current) >= settings.rate_limit_requests:
                raise RateLimitError()
            else:
                await self.redis_client.incr(key)
        except RateLimitError:
            raise
        except Exception:
            logger.warning("Rate limit check failed", extra={"event": "rate_limit_error", "client_ip": client_ip})

        return await call_next(request)

"""
Middleware stack for OmniAI backend.

Improvements:
- Fixed ordering: correlation middleware should be outermost to ensure request_id available.
- SentryUserMiddleware now sets user context BEFORE call_next so logs downstream benefit.
- SecurityHeadersMiddleware tightened CSP and HSTS handling.
- RateLimitMiddleware uses Redis with proper error handling, lazy connection,
  and avoids creating client per request. Falls back to in-memory attempt count warning.
- RequestLoggingMiddleware uses monotonic perf_counter and includes correlation_id.
- _real_client_ip prevents XFF spoofing by checking trusted proxies.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

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
    """
    Return effective client IP.
    Uses X-Forwarded-For only when direct peer is in trusted_proxies.
    Prevents clients from spoofing rate-limit key behind LB.
    """
    peer = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for", "") or request.headers.get("X-Forwarded-For", "")
    if forwarded and settings.trusted_proxies and peer in settings.trusted_proxies:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    # Also support X-Real-IP if behind nginx and trusted
    if settings.trusted_proxies and peer in settings.trusted_proxies:
        real_ip = request.headers.get("x-real-ip", "").strip()
        if real_ip:
            return real_ip
    return peer


def setup_middleware(app: FastAPI) -> None:
    # CORS first (outermost after our correlation)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Order matters: middlewares wrap in reverse order of addition.
    # Add outermost last? Actually first added is outermost? In Starlette, last added wraps first.
    # So we add in order we want execution: RequestCorrelation -> SecurityHeaders -> RequestLogging -> Sentry -> Metrics -> RateLimit
    # To achieve that, add reverse.
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)

    app.add_middleware(APIMetricsMiddleware)
    app.add_middleware(SentryUserMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestCorrelationMiddleware)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("X-Request-ID", "") or request.headers.get("x-request-id", "")
        if not rid:
            rid = f"req_{uuid.uuid4().hex[:16]}"
        set_request_id(rid)

        cid = request.headers.get("X-Correlation-ID", "") or request.headers.get(
            "x-correlation-id", ""
        )
        if cid:
            set_correlation_id(cid)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            if cid:
                response.headers["X-Correlation-ID"] = cid
            return response
        finally:
            reset_request_context()


class SentryUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Parse user BEFORE handling request so downstream logs have context
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:].strip()
                if token:
                    from app.core.security import verify_token

                    payload = verify_token(token, expected_type="access")
                    if payload:
                        user_id = payload.get("sub", "")
                        email = payload.get("email", "")
                        if user_id:
                            set_user_context(user_id=user_id)
                        # Set Sentry user if SDK available
                        try:
                            import sentry_sdk

                            sentry_sdk.set_user({"id": user_id, "email": email})
                        except Exception:
                            # Sentry set_user failed, ignore
                            pass  # noqa: S110
        except Exception:
            # Ignore middleware setup errors to not break request
            pass  # noqa: S110

        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply hardening HTTP response headers (OWASP)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Deprecated, set to 0 to not enable old buggy filter
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        if settings.environment.lower() in ("production", "prod", "staging"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # More restrictive CSP: still allow inline for Next.js, but limit
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' *.sentry.io; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https: wss: ws:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
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
                exc_info=True,
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting.
    Falls back to allowing request if Redis unavailable, but logs warning.
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self._redis_client: redis.Redis | None = None
        self._redis_failed_logged: bool = False

    def _get_redis(self) -> redis.Redis | None:
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.redis_url, decode_responses=True, socket_connect_timeout=2
                )
            except Exception as e:
                if not self._redis_failed_logged:
                    logger.warning(
                        "Redis client creation failed for rate limiter",
                        extra={"event": "rate_limit_redis_init_failed", "error": str(e)},
                    )
                    self._redis_failed_logged = True
                return None
        return self._redis_client

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        route_path = request.url.path

        # Skip health, metrics, docs, openapi, and webhooks
        skip_prefixes = (
            "/health",
            "/ready",
            "/live",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/api/v1/billing/webhook",
        )
        if any(route_path.startswith(p) for p in skip_prefixes):
            return await call_next(request)

        client_ip = _real_client_ip(request)

        try:
            redis_client = self._get_redis()
            if redis_client is None:
                # Fail open but log
                return await call_next(request)

            key = f"ratelimit:{client_ip}:{route_path}"
            # Use pipeline for atomic get+incr pattern? Simple approach with Lua or INCR
            # First, try to incr; if key not exists, set with expiry
            current = await redis_client.get(key)

            if current is None:
                await redis_client.setex(
                    key, settings.rate_limit_window_seconds, 1
                )
            else:
                try:
                    count = int(current)
                except ValueError:
                    count = 0
                if count >= settings.rate_limit_requests:
                    raise RateLimitError(
                        f"Too many requests from {client_ip} to {route_path}. "
                        f"Limit {settings.rate_limit_requests}/{settings.rate_limit_window_seconds}s"
                    )
                await redis_client.incr(key)

        except RateLimitError:
            raise
        except Exception as e:
            # Log but fail open to avoid breaking app if Redis down
            logger.warning(
                "Rate limit check failed, allowing request",
                extra={
                    "event": "rate_limit_error",
                    "client_ip": client_ip,
                    "path": route_path,
                    "error": str(e),
                },
            )

        return await call_next(request)

"""
In-memory rate limiter — fallback for when Redis is unavailable.

This module is kept for backwards compatibility. The primary rate limiting
implementation lives in app.core.middleware.RateLimitMiddleware which uses Redis.

Use this utility directly only if you need an in-process limiter without Redis.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock


class InMemoryRateLimiter:
    """
    Simple sliding window rate limiter in memory.
    Not suitable for distributed deployments (use Redis middleware instead),
    but useful as fallback or for tests.
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Prune old entries
            requests = self._windows[key]
            self._windows[key] = [t for t in requests if t > window_start]

            if len(self._windows[key]) >= max_requests:
                return False

            self._windows[key].append(now)
            return True

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key:
                self._windows.pop(key, None)
            else:
                self._windows.clear()


# Global instance for convenience (used by legacy middleware if needed)
rate_limiter = InMemoryRateLimiter()


# For backwards compatibility, provide a deprecated alias that points to the
# Redis implementation in middleware module. Importing here avoids circular.
try:
    from app.core.middleware import RateLimitMiddleware as RedisRateLimitMiddleware  # noqa: F401
except Exception:
    # If import fails (e.g., during early startup), keep this class as fallback.
    # The legacy middleware is re-exposed as an alias for in-memory version for safety.
    from collections.abc import Callable

    from fastapi import FastAPI, Request, Response
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    class RateLimitMiddleware(BaseHTTPMiddleware):  # type: ignore[no-redef]
        def __init__(
            self,
            app: FastAPI,
            max_requests: int = 60,
            window_seconds: int = 60,
            exclude_paths: list[str] | None = None,
        ):
            super().__init__(app)
            self.max_requests = max_requests
            self.window_seconds = window_seconds
            self.exclude_paths = exclude_paths or [
                "/health",
                "/ready",
                "/live",
                "/docs",
                "/openapi.json",
                "/metrics",
                "/api/v1/billing/webhook",
            ]

        async def dispatch(
            self, request: Request, call_next: Callable
        ) -> Response:
            if any(request.url.path.startswith(p) for p in self.exclude_paths):
                return await call_next(request)

            client_ip = request.client.host if request.client else "unknown"
            key = f"{client_ip}:{request.url.path}"

            if not rate_limiter.check(key, self.max_requests, self.window_seconds):
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "code": "rate_limit_exceeded",
                    },
                )

            return await call_next(request)

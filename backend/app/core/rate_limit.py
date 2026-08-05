import time
from collections import defaultdict
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware



class InMemoryRateLimiter:
    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds

        requests = self._windows[key]
        self._windows[key] = [t for t in requests if t > window_start]

        if len(self._windows[key]) >= max_requests:
            return False

        self._windows[key].append(now)
        return True


rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
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
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/api/v1/billing/webhook"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"

        if not rate_limiter.check(key, self.max_requests, self.window_seconds):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later.", "code": "rate_limit_exceeded"},
            )

        return await call_next(request)

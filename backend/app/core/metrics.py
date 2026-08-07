import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

registry = CollectorRegistry(auto_describe=True)

api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    labelnames=["method", "endpoint", "status_code"],
    registry=registry,
)

api_errors_total = Counter(
    "api_errors_total",
    "Total API errors",
    labelnames=["method", "endpoint", "status_code"],
    registry=registry,
)

api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=registry,
)

active_users = Gauge(
    "active_users",
    "Currently active users",
    registry=registry,
)

ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI requests",
    labelnames=["model", "provider", "status"],
    registry=registry,
)

ai_tokens_used_total = Counter(
    "ai_tokens_used_total",
    "Total AI tokens consumed",
    labelnames=["model", "provider", "token_type"],
    registry=registry,
)

ai_response_latency_seconds = Histogram(
    "ai_response_latency_seconds",
    "AI response latency in seconds",
    labelnames=["model", "provider"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
    registry=registry,
)

ai_model_usage_total = Counter(
    "ai_model_usage_total",
    "AI model usage count",
    labelnames=["model", "provider"],
    registry=registry,
)

ai_context_size_bytes = Histogram(
    "ai_context_size_bytes",
    "AI context size in bytes",
    labelnames=["model"],
    buckets=(1024, 4096, 16384, 65536, 262144, 1048576),
    registry=registry,
)

ai_cost_estimate_total = Counter(
    "ai_cost_estimate_total",
    "Estimated AI cost in USD",
    labelnames=["model", "provider"],
    registry=registry,
)

db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
    registry=registry,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    labelnames=["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=registry,
)

db_errors_total = Counter(
    "db_errors_total",
    "Total database errors",
    labelnames=["query_type"],
    registry=registry,
)

celery_queue_size = Gauge(
    "celery_queue_size",
    "Celery queue size per queue name",
    labelnames=["queue"],
    registry=registry,
)

celery_jobs_processed_total = Counter(
    "celery_jobs_processed_total",
    "Total Celery jobs processed",
    labelnames=["queue", "status"],
    registry=registry,
)

celery_job_duration_seconds = Histogram(
    "celery_job_duration_seconds",
    "Celery job duration in seconds",
    labelnames=["queue", "task"],
    buckets=(0.1, 0.5, 1.0, 5.0, 30.0, 60.0, 300.0, 600.0),
    registry=registry,
)

connector_sync_failures_total = Counter(
    "connector_sync_failures_total",
    "Total connector sync failures",
    labelnames=["connector_type", "error_code"],
    registry=registry,
)

connector_active_integrations = Gauge(
    "connector_active_integrations",
    "Active connector integrations",
    labelnames=["connector_type"],
    registry=registry,
)


class APIMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        method = request.method
        endpoint = request.url.path
        start = time.perf_counter()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            duration = time.perf_counter() - start

            api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            if 500 <= response.status_code < 600:
                api_errors_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

            return response
        except Exception:
            status_code = "500"
            duration = time.perf_counter() - start
            api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            api_errors_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            raise


def track_ai_request(
    model: str,
    provider: str,
    status: str,
    duration_ms: float,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    context_size: int = 0,
    cost_estimate: float = 0.0,
) -> None:
    ai_requests_total.labels(model=model, provider=provider, status=status).inc()
    ai_model_usage_total.labels(model=model, provider=provider).inc()
    ai_response_latency_seconds.labels(model=model, provider=provider).observe(duration_ms / 1000.0)

    if tokens_prompt:
        ai_tokens_used_total.labels(model=model, provider=provider, token_type="prompt").inc(tokens_prompt)  # noqa: S106 - metric label
    if tokens_completion:
        ai_tokens_used_total.labels(model=model, provider=provider, token_type="completion").inc(tokens_completion)  # noqa: S106 - metric label
    if context_size:
        ai_context_size_bytes.labels(model=model).observe(context_size)
    if cost_estimate:
        ai_cost_estimate_total.labels(model=model, provider=provider).inc(cost_estimate)


def track_db_query(query_type: str, duration_ms: float, error: bool = False) -> None:
    db_query_duration_seconds.labels(query_type=query_type).observe(duration_ms / 1000.0)
    if error:
        db_errors_total.labels(query_type=query_type).inc()

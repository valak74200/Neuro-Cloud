import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )
except Exception:  # pragma: no cover - optional at import time during type check
    Counter = None  # type: ignore
    Histogram = None  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain"

    def generate_latest() -> bytes:  # type: ignore
        return b""


logger = logging.getLogger("app.observability")


REQUEST_COUNT = (
    Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
    if Counter
    else None
)
REQUEST_LATENCY = (
    Histogram(
        "http_request_latency_seconds", "HTTP request latency", ["method", "path"]
    )
    if Histogram
    else None
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware to add request id, record metrics, and structured logs."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:  # type: ignore[override]
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        response: Response | None = None
        status_code: int = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed_s = time.perf_counter() - start_time
            # Determine path template if available
            route = request.scope.get("route")
            path_template = getattr(route, "path", request.url.path)

            # Metrics
            if REQUEST_COUNT is not None:
                REQUEST_COUNT.labels(
                    method=request.method,
                    path=path_template,
                    status=str(status_code),
                ).inc()
            if REQUEST_LATENCY is not None:
                REQUEST_LATENCY.labels(
                    method=request.method,
                    path=path_template,
                ).observe(elapsed_s)

            # Logging
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "path_template": path_template,
                    "status": status_code,
                    "duration_ms": int(elapsed_s * 1000),
                    "request_id": request_id,
                },
            )

            # Ensure response has request id header
            if response is not None:
                response.headers.setdefault("X-Request-ID", request_id)


def setup_logging() -> None:
    """Basic logging configuration suitable for CI and local dev."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    # Ensure our logger is at INFO
    logger.setLevel(logging.INFO)


def register_metrics_endpoint(app: FastAPI) -> None:
    """Register `/metrics` endpoint exposing Prometheus metrics."""

    @app.get("/metrics")
    async def metrics() -> Response:
        payload = generate_latest()
        return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


def setup_observability(app: FastAPI) -> None:
    """Setup logging, metrics, and observability middleware for the app."""
    setup_logging()
    app.add_middleware(ObservabilityMiddleware)
    register_metrics_endpoint(app)

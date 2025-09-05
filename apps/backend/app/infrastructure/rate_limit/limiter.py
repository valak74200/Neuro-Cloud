import asyncio
import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


@dataclass
class WindowConfig:
    max_requests: int
    window_seconds: int


def load_config_from_env() -> WindowConfig:
    """Load rate limit configuration from environment variables with safe defaults."""
    max_requests = int(os.getenv("NC_RATE_LIMIT_MAX_REQUESTS", "60"))
    window_seconds = int(os.getenv("NC_RATE_LIMIT_WINDOW_SECONDS", "60"))
    return WindowConfig(max_requests=max_requests, window_seconds=window_seconds)


class SlidingWindowRateLimiter:
    """Simple in-memory sliding-window limiter keyed by string (user or IP)."""

    def __init__(self, config: Optional[WindowConfig] = None) -> None:
        self._config = config or load_config_from_env()
        self._key_to_hits: Dict[str, Deque[float]] = {}
        self._lock = asyncio.Lock()

    def _now(self) -> float:
        return time.monotonic()

    async def is_allowed(self, key: str) -> tuple[bool, int, int, int]:
        """Return (allowed, limit, remaining, reset_seconds)."""
        async with self._lock:
            window = self._key_to_hits.get(key)
            if window is None:
                window = deque()
                self._key_to_hits[key] = window

            now = self._now()
            cutoff = now - self._config.window_seconds
            # prune old hits
            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) < self._config.max_requests:
                window.append(now)
                remaining = self._config.max_requests - len(window)
                reset = max(0, int(self._config.window_seconds - (now - window[0])))
                return True, self._config.max_requests, remaining, reset

            # rate limited
            reset = max(0, int(self._config.window_seconds - (now - window[0])))
            remaining = 0
            return False, self._config.max_requests, remaining, reset


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces per-user or per-IP rate limits with headers."""

    def __init__(
        self, app: ASGIApp, limiter: Optional[SlidingWindowRateLimiter] = None
    ) -> None:
        super().__init__(app)
        self._limiter = limiter or SlidingWindowRateLimiter()

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        key = self._resolve_key(request)
        allowed, limit, remaining, reset = await self._limiter.is_allowed(key)
        if not allowed:
            response = Response(status_code=429, content="Too Many Requests")
            self._apply_headers(response, limit, remaining, reset)
            response.headers.setdefault("Retry-After", str(max(1, reset)))
            return response

        response = await call_next(request)
        self._apply_headers(response, limit, remaining, reset)
        return response

    def _resolve_key(self, request: Request) -> str:
        # Prefer user id if present (set by auth middleware) else IP
        user_id = None
        try:
            claims = getattr(request.state, "user_claims", None)
            if claims is not None:
                user_id = getattr(claims, "user_id", None)
            if user_id is None:
                user = getattr(request.state, "user", None)
                user_id = getattr(user, "id", None)
        except Exception:
            user_id = None

        if user_id:
            return f"user:{user_id}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    @staticmethod
    def _apply_headers(
        response: Response, limit: int, remaining: int, reset: int
    ) -> None:
        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers.setdefault("X-RateLimit-Reset", str(reset))

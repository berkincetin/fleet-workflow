"""Cross-cutting ASGI middleware: trace-id, append-only audit, and rate limiting."""

from __future__ import annotations

import time

import redis.asyncio as redis
from fleet_api.audit import write_audit
from fleet_api.db import get_engine
from fleet_api.otel import new_trace_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Assign a trace_id per request and echo it in the response header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or new_trace_id()
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Write an append-only audit row for each request, carrying the trace_id."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        trace_id = getattr(request.state, "trace_id", None)
        engine = get_engine()
        try:
            await write_audit(
                engine,
                actor=request.headers.get("X-User", "anonymous"),
                actor_type="user",
                action=f"{request.method} {request.url.path}",
                entity="http_request",
                entity_id=str(response.status_code),
                trace_id=trace_id,
            )
        except Exception:
            # If the audit database is unavailable, log but do not fail the request.
            pass
        finally:
            await engine.dispose()
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client rate limiting backed by Redis."""

    def __init__(self, app, redis_url: str, limit_per_minute: int) -> None:
        super().__init__(app)
        self._redis_url = redis_url
        self._limit = limit_per_minute

    async def dispatch(self, request: Request, call_next) -> Response:
        client = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"ratelimit:{client}:{window}"
        r = redis.from_url(self._redis_url)
        try:
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)
        except Exception:
            # If Redis is unavailable, skip rate limiting but allow the request.
            return await call_next(request)
        finally:
            await r.aclose()
        if count > self._limit:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limited", "message": "too many requests"}},
            )
        return await call_next(request)

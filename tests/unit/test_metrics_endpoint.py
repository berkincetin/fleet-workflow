"""GET /metrics (task 7.4): unauthenticated Prometheus exposition endpoint.
Proves the route works and that request metrics recorded by
RequestMetricsMiddleware show up in the scrape output, using a route-path
template label (not the raw resolved path) so per-request path params never
create unbounded label cardinality.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.middleware import RequestMetricsMiddleware
from fleet_api.routers import metrics as metrics_router


class _FakeResult:
    def all(self) -> list[object]:
        return []


class _FakeSession:
    async def execute(self, *_args: object, **_kwargs: object) -> _FakeResult:
        return _FakeResult()


class _FakeRedis:
    async def zcard(self, _key: str) -> int:
        return 0

    async def aclose(self) -> None:
        pass


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestMetricsMiddleware)
    app.include_router(metrics_router.router)

    async def fake_get_session():  # type: ignore[no-untyped-def]
        yield _FakeSession()

    app.dependency_overrides[metrics_router.get_session] = fake_get_session
    app.dependency_overrides[metrics_router.get_ingest_redis] = lambda: _FakeRedis()

    @app.get("/v1/widgets/{widget_id}")
    async def widget(widget_id: int) -> dict[str, int]:
        return {"id": widget_id}

    return app


def test_metrics_endpoint_returns_prometheus_exposition_format() -> None:
    client = TestClient(_build_app())
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]


def test_request_metrics_use_route_template_not_raw_path() -> None:
    client = TestClient(_build_app())
    client.get("/v1/widgets/123")
    client.get("/v1/widgets/456")

    body = client.get("/metrics").text
    assert 'path="/v1/widgets/{widget_id}"' in body
    assert "/v1/widgets/123" not in body
    assert "/v1/widgets/456" not in body

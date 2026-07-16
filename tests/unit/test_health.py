"""Unit test: healthz returns ok without any external dependency."""

from fastapi.testclient import TestClient
from fleet_api.app import create_app


def test_healthz_ok() -> None:
    client = TestClient(create_app(with_middleware=False))
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

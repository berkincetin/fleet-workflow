"""Integration: `/v1/admin/services` against the real dev stack (task 13.3 AC).

The AC is about live state, so the probes run for real: with `make dev` up,
every non-optional service must report healthy, and the response must never
carry a usable credential. In-process via httpx.ASGITransport, the same pattern
the other admin live tests use.
"""

from __future__ import annotations

import os

import httpx
import pytest

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"


def _stack_up() -> bool:
    try:
        resp = httpx.get(
            f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3
        )
        return resp.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _stack_up(), reason="dev stack not reachable — start with `make dev`"
)


def _token(username: str, password: str) -> str:
    resp = httpx.post(
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "client_secret": "fleet-api-dev-secret",
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


def _app():
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    from fleet_api.app import create_app
    from fleet_api.db import reset_engine_cache

    reset_engine_cache()
    return create_app(with_middleware=False)


async def test_every_non_optional_service_reports_healthy() -> None:
    token = _token("admin", "admin")
    transport = httpx.ASGITransport(app=_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/v1/admin/services", headers={"Authorization": f"Bearer {token}"}, timeout=60
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    unhealthy = [
        s["name"] for s in body["services"] if not s["optional"] and s["status"] != "healthy"
    ]
    assert unhealthy == [], f"stack is up but these report unhealthy: {unhealthy}"
    assert body["down"] == 0

    # Queue/worker state is part of the AC, not just container liveness.
    workers = {s["name"]: s for s in body["services"] if s["group"] == "worker"}
    assert set(workers) == {"n8n-worker", "arq"}
    assert workers["n8n-worker"]["status"] == "healthy"
    assert workers["n8n-worker"]["queue_depth"] is not None


async def test_no_plaintext_credential_is_ever_in_the_list_response() -> None:
    token = _token("admin", "admin")
    transport = httpx.ASGITransport(app=_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/v1/admin/services", headers={"Authorization": f"Bearer {token}"}, timeout=60
        )
    assert resp.status_code == 200

    # The compose defaults are what a real deployment would have replaced; if
    # any of them appears verbatim, masking has failed.
    for secret in ("fleet_dev_pw", "sk-fleet-dev-master", "sk-lf-fleet-dev"):
        assert secret not in resp.text, f"unmasked secret in the list response: {secret}"

    for service in resp.json()["services"]:
        for cred in service["credentials"]:
            assert "secret" not in cred
            assert cred["secret_masked"] is None or "•" in cred["secret_masked"]


async def test_builder_is_refused_and_platform_admin_can_reveal() -> None:
    transport = httpx.ASGITransport(app=_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        builder = await client.get(
            "/v1/admin/services",
            headers={"Authorization": f"Bearer {_token('builder', 'builder')}"},
            timeout=60,
        )
        revealed = await client.post(
            "/v1/admin/services/postgres/reveal",
            headers={"Authorization": f"Bearer {_token('admin', 'admin')}"},
            timeout=30,
        )
    assert builder.status_code == 403
    assert "fleet_dev_pw" not in builder.text

    assert revealed.status_code == 200, revealed.text
    assert revealed.json()["credentials"][0]["secret"]

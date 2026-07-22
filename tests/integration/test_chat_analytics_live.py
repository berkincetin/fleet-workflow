"""Integration: chat endpoint's Analytics reply path against the real dev
stack (task 5.2 AC: "business question -> table + SQL shown"). Uses the
already-seeded `analytics` agent (apps/api/fleet_api/seed.py's
seed_analytics_agent(), run via `make seed`) since the chat endpoint's
Analytics branch is keyed on the literal agent name, and agent names are
unique — this test can't create its own "analytics"-named agent the way
test_chat_live.py creates a fresh agent per run.
"""

from __future__ import annotations

import os

import httpx
import pytest

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _stack_up(), reason="dev stack not reachable — start with `make dev`"
)


def _builder_token() -> str:
    resp = httpx.post(
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "client_secret": "fleet-api-dev-secret",
            "grant_type": "password",
            "username": "builder",
            "password": "builder",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


def _parse_sse(raw: bytes) -> list[tuple[str, dict]]:
    import json

    events: list[tuple[str, dict]] = []
    event_name = None
    for line in raw.decode().splitlines():
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
        elif line.startswith("data:") and event_name:
            events.append((event_name, json.loads(line[len("data:") :].strip())))
            event_name = None
    return events


def test_analytics_reply_shows_sql_for_a_business_question() -> None:
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"
    os.environ["FLEET_REDIS_URL"] = "redis://localhost:6379/0"

    token = _builder_token()

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.app import create_app
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        fleet_db._app_session_factory.cache_clear()

        engine = create_async_engine(API_DATABASE_URL)
        async with engine.connect() as conn:
            row = (
                await conn.execute(text("SELECT id FROM agents WHERE name = 'analytics'"))
            ).first()
        await engine.dispose()
        assert row is not None, "analytics agent not seeded — run `make seed` first"
        agent_id = int(row[0])

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", headers=headers, timeout=30
        ) as client:
            created_conv = await client.post("/v1/conversations", json={"agent_id": agent_id})
            assert created_conv.status_code == 201, created_conv.text
            conv_id = created_conv.json()["id"]

            async with client.stream(
                "POST",
                f"/v1/conversations/{conv_id}/messages",
                json={"content": "List all sales"},
            ) as resp:
                assert resp.status_code == 200
                raw = b""
                async for chunk in resp.aiter_bytes():
                    raw += chunk

            events = _parse_sse(raw)
            token_events = [d["delta"] for name, d in events if name == "token"]
            assert token_events, "expected at least one token event"
            full_text = "".join(token_events)

            # The literal AC: generated SQL is always shown to the user.
            assert "SELECT" in full_text
            assert "fixture_sales" in full_text

            done_events = [d for name, d in events if name == "done"]
            assert done_events, "expected a done event"

    import asyncio

    asyncio.run(_run())

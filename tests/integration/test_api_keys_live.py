"""Integration: Fleet API key auth against the real dev stack (task 6.1 AC).

AC (docs/split/implementation-plan/sprint-6-n8n-automations.md): "a trivial
workflow executes on a worker and calls the Fleet API with an issued key; a
revoked key gets 401." The n8n-workflow half of this AC was proven manually
this session (real oauth2-proxy Keycloak login -> real n8n workflow execution
-> real `/v1/service/pg-query` call -> real row data back; then a revoked key
re-run of the same call -> 401) — n8n itself isn't something pytest drives.
This file locks in the API-side half: issuing (via direct SQL, see below),
using, and revoking a key against the real Postgres + real pg_ro path.

`POST /v1/admin/api-keys` needs MANAGE_PLATFORM, which — per the pre-existing
Sprint-3/4/5 role-string gap already logged in PROGRESS.md (no seeded
Keycloak user holds the exact `platform_admin` role) — cannot be exercised
through the real HTTP API yet. Worked around the same way those admin routers
were: the key row is seeded directly via SQL (using the real `api_keys`
hashing helpers, not a hand-rolled hash), and only the *validation/enforcement*
path — the part the AC actually cares about — goes through the real HTTP API.
"""

from __future__ import annotations

import datetime as dt
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


def test_valid_key_authenticates_and_revoked_key_gets_401() -> None:
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.api_keys import generate_key, hash_key
        from fleet_api.app import create_app
        from fleet_api.models import ApiKey
        from sqlalchemy import delete

        # See test_rag_pii_collection_live.py for why this is required across
        # test modules on Windows (cached engine bound to a closed event loop).
        fleet_db._app_session_factory.cache_clear()

        raw_key = generate_key()
        session_factory = fleet_db._app_session_factory()
        async with session_factory() as session:
            row = ApiKey(name="live-test-key", hash=hash_key(raw_key), scopes=["pg_ro"])
            session.add(row)
            await session.commit()
            await session.refresh(row)
            key_id = row.id

        try:
            app = create_app(with_middleware=False)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                # Missing key -> 401, no header at all.
                no_key = await client.post(
                    "/v1/service/pg-query", json={"sql": "SELECT COUNT(*) AS n FROM fixture_sales"}
                )
                assert no_key.status_code == 401

                # Valid key -> the real pg_ro path runs, real row count back.
                ok = await client.post(
                    "/v1/service/pg-query",
                    json={"sql": "SELECT COUNT(*) AS n FROM fixture_sales"},
                    headers={"X-Fleet-Api-Key": raw_key},
                )
                assert ok.status_code == 200, ok.text
                assert ok.json()["row_count"] == 1

                # Revoke -> the same previously-valid key now gets 401.
                async with session_factory() as session:
                    row = await session.get(ApiKey, key_id)
                    assert row is not None
                    row.revoked_at = dt.datetime.now(dt.UTC)
                    await session.commit()

                revoked = await client.post(
                    "/v1/service/pg-query",
                    json={"sql": "SELECT COUNT(*) AS n FROM fixture_sales"},
                    headers={"X-Fleet-Api-Key": raw_key},
                )
                assert revoked.status_code == 401
        finally:
            async with session_factory() as session:
                await session.execute(delete(ApiKey).where(ApiKey.name == "live-test-key"))
                await session.commit()

    import asyncio

    asyncio.run(_run())


def test_key_without_required_scope_gets_403() -> None:
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.api_keys import generate_key, hash_key
        from fleet_api.app import create_app
        from fleet_api.models import ApiKey
        from sqlalchemy import delete

        fleet_db._app_session_factory.cache_clear()

        raw_key = generate_key()
        session_factory = fleet_db._app_session_factory()
        async with session_factory() as session:
            row = ApiKey(name="live-test-no-scope", hash=hash_key(raw_key), scopes=[])
            session.add(row)
            await session.commit()

        try:
            app = create_app(with_middleware=False)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/v1/service/pg-query",
                    json={"sql": "SELECT COUNT(*) AS n FROM fixture_sales"},
                    headers={"X-Fleet-Api-Key": raw_key},
                )
                assert resp.status_code == 403
        finally:
            async with session_factory() as session:
                await session.execute(delete(ApiKey).where(ApiKey.name == "live-test-no-scope"))
                await session.commit()

    import asyncio

    asyncio.run(_run())

"""Integration: /v1/admin/cost/summary and /v1/admin/audit (task 7.2) against
real Postgres — real aggregation queries over spend_ledger/audit_log, the
demo seed's idempotency, and the Langfuse deep-link URL builder. RBAC-shape/
validation is already unit-tested (tests/unit/test_observability_admin_router.py).
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.db import get_engine, reset_engine_cache
from fleet_api.errors import install_error_handlers
from fleet_api.routers import observability_admin as observability_admin_router
from fleet_api.seed import seed, seed_observability_demo
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def migrated_pg() -> str:
    with PostgresContainer("postgres:16") as pg:
        raw = pg.get_connection_url()
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        os.environ["FLEET_DATABASE_URL"] = raw.replace("+psycopg2", "+asyncpg")
        asyncio.run(seed())
        asyncio.run(seed_observability_demo())
        asyncio.run(seed_observability_demo())  # must not duplicate
        yield os.environ["FLEET_DATABASE_URL"]


@pytest.fixture()
def client(migrated_pg: str):
    reset_engine_cache()
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(observability_admin_router.router)

    async def fake_current_user() -> CurrentUser:
        return CurrentUser(sub="admin-caller", roles={"platform_admin"})

    app.dependency_overrides[get_current_user] = fake_current_user
    with TestClient(app) as c:
        yield c


def test_seed_observability_demo_is_idempotent(migrated_pg: str) -> None:
    engine = get_engine()

    async def _count() -> int:
        async with engine.connect() as conn:
            return (
                await conn.execute(
                    text("SELECT count(*) FROM spend_ledger WHERE trace_id LIKE 'demo-seed-%'")
                )
            ).scalar_one()

    count = asyncio.run(_count())
    asyncio.run(engine.dispose())
    assert count == 60  # exactly one seeded batch despite two seed() calls


def test_cost_summary_renders_seeded_traffic(client: TestClient) -> None:
    resp = client.get("/v1/admin/cost/summary", params={"days": 30})
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_usd"] > 0
    assert len(body["by_dept"]) >= 1
    # Derived from the seeder rather than hardcoded: this assertion was a
    # literal `== 4` and broke the moment task 8.5 legitimately seeded
    # hr_agent + hr_onboarding, even though the cost summary was correct.
    from fleet_api.seed import _DEMO_AGENTS

    assert len(body["by_agent"]) == len(_DEMO_AGENTS)
    assert len(body["by_model"]) == 3
    assert len(body["burn_down"]) >= 1
    assert 0 <= body["cache_hit_ratio"] <= 1


def test_audit_list_includes_langfuse_deep_link(client: TestClient) -> None:
    resp = client.get("/v1/admin/audit", params={"limit": 500})
    assert resp.status_code == 200
    rows = resp.json()

    demo_rows = [r for r in rows if r["trace_id"] and r["trace_id"].startswith("demo-seed-")]
    assert len(demo_rows) > 0
    row = demo_rows[0]
    assert row["langfuse_url"] == f"http://localhost:3001/project/fleet-dev/traces/{row['trace_id']}"


def test_audit_filter_by_actor(client: TestClient) -> None:
    resp = client.get("/v1/admin/audit", params={"actor": "demo-user", "limit": 500})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) > 0
    assert all(r["actor"] == "demo-user" for r in rows)

"""Integration: /v1/admin/budgets (task 7.1b) against real Postgres — create,
list, update, delete, and the DB-level uniqueness constraint on
(scope_type, scope_id, period) from migration 0003. RBAC-shape/validation is
already unit-tested (tests/unit/test_budgets_admin_router.py).
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
import sqlalchemy
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.db import reset_engine_cache
from fleet_api.errors import install_error_handlers
from fleet_api.routers import budgets_admin as budgets_admin_router
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

_sync_pg_url: str = ""


@pytest.fixture(scope="module")
def migrated_pg() -> str:
    global _sync_pg_url
    with PostgresContainer("postgres:16") as pg:
        raw = pg.get_connection_url()
        _sync_pg_url = raw
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        os.environ["FLEET_DATABASE_URL"] = raw.replace("+psycopg2", "+asyncpg")
        yield os.environ["FLEET_DATABASE_URL"]


def _insert_spend(dept_id: str, cost_usd: float) -> None:
    """Plain sync insert (psycopg2, no asyncio) — see test_users_admin_router_live.py's
    _insert_user for why: never share an event loop with the async TestClient
    calls in the same test."""
    engine = sqlalchemy.create_engine(_sync_pg_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO spend_ledger (model, dept_id, tok_in, tok_out, cost_usd) "
                    "VALUES ('utility', :d, 100, 50, :c)"
                ),
                {"d": dept_id, "c": cost_usd},
            )
    finally:
        engine.dispose()


@pytest.fixture()
def client(migrated_pg: str):
    reset_engine_cache()
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(budgets_admin_router.router)

    async def fake_current_user() -> CurrentUser:
        return CurrentUser(sub="admin-caller", roles={"platform_admin"})

    app.dependency_overrides[get_current_user] = fake_current_user
    with TestClient(app) as c:
        yield c


def test_create_then_list_then_update_then_delete(client: TestClient) -> None:
    resp = client.post(
        "/v1/admin/budgets",
        json={"scope_type": "dept", "scope_id": "1", "limit_usd": 500.0, "soft_pct": 75},
    )
    assert resp.status_code == 201
    budget_id = resp.json()["id"]

    listed = client.get("/v1/admin/budgets").json()
    assert any(b["id"] == budget_id and b["limit_usd"] == 500.0 for b in listed)

    resp = client.patch(
        f"/v1/admin/budgets/{budget_id}",
        json={"scope_type": "dept", "scope_id": "1", "limit_usd": 750.0, "soft_pct": 80},
    )
    assert resp.status_code == 200
    assert resp.json()["limit_usd"] == 750.0

    resp = client.delete(f"/v1/admin/budgets/{budget_id}")
    assert resp.status_code == 204

    listed = client.get("/v1/admin/budgets").json()
    assert all(b["id"] != budget_id for b in listed)


def test_duplicate_scope_and_period_rejected(client: TestClient) -> None:
    client.post(
        "/v1/admin/budgets",
        json={"scope_type": "agent", "scope_id": "42", "limit_usd": 100.0},
    )
    resp = client.post(
        "/v1/admin/budgets",
        json={"scope_type": "agent", "scope_id": "42", "limit_usd": 200.0},
    )
    assert resp.status_code == 409


def test_global_budget_has_no_scope_id(client: TestClient) -> None:
    resp = client.post(
        "/v1/admin/budgets",
        json={"scope_type": "global", "scope_id": None, "limit_usd": 10000.0},
    )
    assert resp.status_code == 201
    assert resp.json()["scope_id"] is None


def test_list_reports_soft_exceeded_from_real_spend(client: TestClient) -> None:
    """Task 7.4's "UI warning" half of the soft-limit AC: list_budgets
    computes real current-period spend against each budget (reusing
    core.llm.budget.check_budget, the same function task 2.4's enforcement
    pre-check uses), so the admin UI can show a warning the moment a scope
    crosses its soft limit — not just on the next LLM call."""
    client.post(
        "/v1/admin/budgets",
        json={"scope_type": "dept", "scope_id": "99", "limit_usd": 100.0, "soft_pct": 80},
    )
    _insert_spend("99", 85.0)  # 85% of a $100 limit -> over the 80% soft threshold

    listed = client.get("/v1/admin/budgets").json()
    row = next(b for b in listed if b["scope_type"] == "dept" and b["scope_id"] == "99")
    assert row["spent_usd"] == 85.0
    assert row["soft_exceeded"] is True
    assert row["hard_exceeded"] is False

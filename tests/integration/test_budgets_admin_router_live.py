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
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.db import reset_engine_cache
from fleet_api.errors import install_error_handlers
from fleet_api.routers import budgets_admin as budgets_admin_router
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
        yield os.environ["FLEET_DATABASE_URL"]


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

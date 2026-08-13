"""Integration: /v1/admin/users and /v1/admin/departments (task 7.1) against
real Postgres — list with joined roles, dept reassignment, role add/remove,
and department listing. RBAC-shape/validation is already unit-tested
(tests/unit/test_users_admin_router.py); this proves the real multi-table
queries.
"""

from __future__ import annotations

import asyncio
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
from fleet_api.routers import users_admin as users_admin_router
from fleet_api.seed import seed
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
        asyncio.run(seed())
        yield os.environ["FLEET_DATABASE_URL"]


@pytest.fixture()
def client(migrated_pg: str):
    # Bare TestClient(app) opens a brand-new event loop (a new anyio blocking
    # portal) for *every single call* when not used as a context manager —
    # fine for a test that calls it once, but db.py's engine is cached
    # process-wide, so a second call in the same test reuses an engine bound
    # to the first call's already-closed loop ("Event loop is closed").
    # `with TestClient(app) as client:` keeps one portal/loop alive for every
    # call made through it, which is what a multi-call test here needs.
    reset_engine_cache()
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(users_admin_router.router)
    app.include_router(users_admin_router.departments_router)

    async def fake_current_user() -> CurrentUser:
        return CurrentUser(sub="admin-caller", roles={"platform_admin"})

    app.dependency_overrides[get_current_user] = fake_current_user
    with TestClient(app) as c:
        yield c


def _insert_user(kc_sub: str) -> int:
    """Plain sync insert (psycopg2, no asyncio) so this setup never shares an
    event loop with the async TestClient calls in the same test — mixing two
    separate asyncio loops in one test process is what triggers the Windows
    asyncpg "Event loop is closed" flake documented in docs/PROGRESS.md."""
    engine = sqlalchemy.create_engine(_sync_pg_url)
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "INSERT INTO users (kc_sub, email_hash, display_name, status) "
                    "VALUES (:s, '', :s, 'active') RETURNING id"
                ),
                {"s": kc_sub},
            )
            return row.scalar_one()
    finally:
        engine.dispose()


def test_list_users_includes_seeded_admin_row(client: TestClient) -> None:
    resp = client.get("/v1/admin/users")
    assert resp.status_code == 200
    body = resp.json()
    assert any(u["kc_sub"] == "seed-admin" for u in body)


def test_list_departments_returns_seeded_departments(client: TestClient) -> None:
    resp = client.get("/v1/admin/departments")
    assert resp.status_code == 200
    names = {d["name"] for d in resp.json()}
    assert "Finance" in names


def test_add_role_then_list_reflects_it(client: TestClient, migrated_pg: str) -> None:
    user_id = _insert_user("sub-add-role")

    resp = client.post(f"/v1/admin/users/{user_id}/roles", json={"role": "builder"})
    assert resp.status_code == 201
    role_id = resp.json()["id"]

    listed = client.get("/v1/admin/users").json()
    row = next(u for u in listed if u["id"] == user_id)
    assert {r["role"] for r in row["roles"]} == {"builder"}

    resp = client.delete(f"/v1/admin/users/{user_id}/roles/{role_id}")
    assert resp.status_code == 204

    listed = client.get("/v1/admin/users").json()
    row = next(u for u in listed if u["id"] == user_id)
    assert row["roles"] == []


def test_update_dept_reassigns_user(client: TestClient, migrated_pg: str) -> None:
    user_id = _insert_user("sub-dept")
    dept_id = client.get("/v1/admin/departments").json()[0]["id"]

    resp = client.patch(f"/v1/admin/users/{user_id}", json={"dept_id": dept_id})
    assert resp.status_code == 200
    assert resp.json()["dept_id"] == dept_id


def test_duplicate_role_assignment_rejected(client: TestClient, migrated_pg: str) -> None:
    user_id = _insert_user("sub-dup-role")
    client.post(f"/v1/admin/users/{user_id}/roles", json={"role": "approver"})

    resp = client.post(f"/v1/admin/users/{user_id}/roles", json={"role": "approver"})
    assert resp.status_code == 409

"""Integration test: `alembic upgrade head` creates the core tables and the readonly role."""

from __future__ import annotations

import os
import subprocess
import sys

import psycopg2
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def pg_url() -> str:
    with PostgresContainer("postgres:16") as pg:
        # testcontainers gives a psycopg2 URL; expose it for Alembic via env.
        raw = pg.get_connection_url()  # postgresql+psycopg2://test:test@host:port/test
        os.environ["FLEET_DATABASE_URL"] = raw
        yield raw


def test_migration_creates_core_tables(pg_url: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "infra/migrations/alembic.ini", "upgrade", "head"],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert result.returncode == 0, result.stderr

    conn = psycopg2.connect(pg_url.replace("+psycopg2", ""))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public';"
        )
        tables = {row[0] for row in cur.fetchall()}
        assert {"departments", "users", "roles", "audit_log"} <= tables
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'fleet_readonly';")
        assert cur.fetchone() is not None
    finally:
        conn.close()

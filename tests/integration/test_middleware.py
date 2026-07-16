"""Integration test: an audit row is written with the request trace_id, and the
rate limiter returns 429 past the configured limit."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="module")
def stack():
    with PostgresContainer("postgres:16") as pg, RedisContainer("redis:7") as rc:
        raw = pg.get_connection_url()  # postgresql+psycopg2://...
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        async_url = raw.replace("+psycopg2", "+asyncpg")
        redis_host = rc.get_container_host_ip()
        redis_port = rc.get_exposed_port(6379)
        os.environ["FLEET_DATABASE_URL"] = async_url
        os.environ["FLEET_REDIS_URL"] = f"redis://{redis_host}:{redis_port}/0"
        os.environ["FLEET_RATE_LIMIT_PER_MINUTE"] = "3"
        yield async_url


def test_audit_row_has_trace_id(stack: str) -> None:
    from fleet_api.app import create_app
    from fleet_api.db import get_engine

    client = TestClient(create_app())
    resp = client.get("/healthz")
    assert resp.status_code == 200
    trace_id = resp.headers["X-Trace-Id"]
    assert trace_id

    import asyncio

    async def _check() -> None:
        engine = get_engine()
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("SELECT trace_id FROM audit_log ORDER BY id DESC LIMIT 1")
                )
            ).first()
            assert row is not None
            assert row[0] == trace_id
        await engine.dispose()

    asyncio.run(_check())


def test_rate_limit_429(stack: str) -> None:
    from fleet_api.app import create_app

    client = TestClient(create_app())
    # limit is 3/min; the 4th request in the same window is 429.
    codes = [client.get("/healthz").status_code for _ in range(5)]
    assert 429 in codes

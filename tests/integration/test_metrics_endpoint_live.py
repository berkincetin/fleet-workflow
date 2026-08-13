"""Integration: GET /metrics (task 7.4) against real Postgres + Redis — the
dept daily-spend / 7-day-average gauges (feeding the cost-anomaly alert rule)
computed from real spend_ledger rows, and the queue-depth gauge reading a
real arq-shaped Redis sorted set. Route-template labeling and content-type
are already unit-tested (tests/unit/test_metrics_endpoint.py).
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import pytest
from arq.constants import default_queue_name
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.db import reset_engine_cache
from fleet_api.routers import metrics as metrics_router
from fleet_api.seed import seed, seed_observability_demo
from redis.asyncio import Redis
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


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
        yield os.environ["FLEET_DATABASE_URL"]


@pytest.fixture(scope="module")
def redis_url() -> str:
    with RedisContainer("redis:7") as rc:
        host = rc.get_container_host_ip()
        port = rc.get_exposed_port(6379)
        url = f"redis://{host}:{port}/0"

        async def _seed_queue() -> None:
            client = Redis.from_url(url)
            try:
                await client.zadd(default_queue_name, {"job-1": 1, "job-2": 2, "job-3": 3})
            finally:
                await client.aclose()

        asyncio.run(_seed_queue())
        yield url


@pytest.fixture()
def client(migrated_pg: str, redis_url: str):
    reset_engine_cache()
    os.environ["FLEET_INGEST_REDIS_URL"] = redis_url
    app = FastAPI()
    app.include_router(metrics_router.router)
    with TestClient(app) as c:
        yield c


def test_metrics_includes_dept_daily_spend_from_seeded_traffic(client: TestClient) -> None:
    body = client.get("/metrics").text
    assert "fleet_dept_daily_spend_usd{" in body
    assert "fleet_dept_avg_daily_spend_7d_usd{" in body


def test_metrics_includes_real_queue_depth(client: TestClient) -> None:
    body = client.get("/metrics").text
    assert 'fleet_queue_depth{queue="ingest"} 3.0' in body

"""Integration test: seed inserts departments and creates the analytics fixture views."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import pytest
from fleet_api.db import get_engine
from fleet_api.seed import seed
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def migrated_pg() -> str:
    with PostgresContainer("postgres:16") as pg:
        raw = pg.get_connection_url()  # postgresql+psycopg2://...
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        # seed uses the async engine → hand it the asyncpg URL.
        os.environ["FLEET_DATABASE_URL"] = raw.replace("+psycopg2", "+asyncpg")
        yield os.environ["FLEET_DATABASE_URL"]


def test_seed_populates_and_creates_views(migrated_pg: str) -> None:
    asyncio.run(seed())

    async def _check() -> None:
        engine = get_engine(migrated_pg)
        async with engine.connect() as conn:
            depts = (await conn.execute(text("SELECT count(*) FROM departments"))).scalar_one()
            assert depts >= 5
            sales = (await conn.execute(text("SELECT count(*) FROM fixture_sales"))).scalar_one()
            assert sales == 500
        await engine.dispose()

    asyncio.run(_check())

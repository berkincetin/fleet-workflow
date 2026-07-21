"""Integration: spend_ledger writes + budget pre-check aggregate against a real
Postgres (tasks 2.3/2.4). No cloud keys needed — the LLM transport is faked; what
is exercised for real is the DB: the 0003 migration, the SpendLedger sink, and
DbBudgetChecker's SUM-over-period query."""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def pg_url() -> str:
    with PostgresContainer("postgres:16") as pg:
        raw = pg.get_connection_url()  # postgresql+psycopg2://...
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        yield raw.replace("+psycopg2", "+asyncpg")


def _sf(url: str) -> async_sessionmaker:
    engine = create_async_engine(url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_spend(sf: async_sessionmaker, rows: list[dict]) -> None:
    async with sf() as s:
        for r in rows:
            await s.execute(
                text(
                    "INSERT INTO spend_ledger (model, dept_id, agent_id, user_id, "
                    "tok_in, tok_out, cost_usd, trace_id) VALUES "
                    "(:model, :dept, :agent, :user, :ti, :to, :cost, :tid)"
                ),
                r,
            )
        await s.commit()


def test_spend_ledger_sink_writes_row(pg_url: str) -> None:
    import asyncio

    from core.llm.ledger import SpendLedger

    async def _run() -> None:
        sf = _sf(pg_url)
        await SpendLedger(sf).record(
            {
                "model": "reasoning",
                "agent_id": "support-copilot",
                "user_id": "u-1",
                "dept_id": "cs",
                "tok_in": 100,
                "tok_out": 40,
                "tok_cached": 0,
                "cost_usd": 0.0009,
                "trace_id": "trace-abc",
            }
        )
        async with sf() as s:
            row = (
                await s.execute(
                    text(
                        "SELECT model, cost_usd, trace_id FROM spend_ledger "
                        "WHERE trace_id = 'trace-abc'"
                    )
                )
            ).first()
        assert row is not None
        assert row[0] == "reasoning"
        assert float(row[1]) == pytest.approx(0.0009)

    asyncio.run(_run())


def test_budget_precheck_hard_stops_when_spend_over_limit(pg_url: str) -> None:
    import asyncio

    from core.llm.budget import check_budget

    async def _run() -> None:
        sf = _sf(pg_url)
        # A dept budget of $1 and $2 of spend this month → hard stop.
        async with sf() as s:
            await s.execute(
                text(
                    "INSERT INTO budgets (scope_type, scope_id, period, limit_usd, soft_pct) "
                    "VALUES ('dept', 'finance', 'monthly', 1.00, 80) "
                    "ON CONFLICT DO NOTHING"
                )
            )
            await s.commit()
        now = dt.datetime.now(dt.UTC)
        await _seed_spend(
            sf,
            [
                {"model": "reasoning", "dept": "finance", "agent": None, "user": None,
                 "ti": 1000, "to": 1000, "cost": 2.00, "tid": "b-1"},
            ],
        )
        status = await check_budget(sf, scope_type="dept", scope_id="finance", now=now)
        assert status.hard_exceeded is True
        assert status.allowed is False

    asyncio.run(_run())


def test_budget_precheck_unlimited_when_no_row(pg_url: str) -> None:
    import asyncio

    from core.llm.budget import check_budget

    async def _run() -> None:
        sf = _sf(pg_url)
        status = await check_budget(sf, scope_type="dept", scope_id="no-budget-dept")
        assert status.allowed is True
        assert status.limit_usd is None

    asyncio.run(_run())

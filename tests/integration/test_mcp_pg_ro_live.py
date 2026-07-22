"""Integration: pg_ro MCP tool against the real dev-stack Postgres (task 5.1
AC — "each server passes contract tests"). Proves SET ROLE fleet_readonly
actually works against the granted role (migration 0007) and that the
fixture warehouse views (fixture_sales/fixture_orders, seeded in task 1.2)
are reachable exactly as the Analytics agent (5.2) will need.
"""

from __future__ import annotations

import os

import asyncpg
import pytest
from fleet_mcp.servers.asyncpg_runner import AsyncpgRunner
from fleet_mcp.servers.pg_ro import NonAllowlistedTableError, PgReadOnlyTool

FLEET_DSN = os.environ.get(
    "FLEET_DATABASE_DSN", "postgresql://fleet:fleet_dev_pw@localhost:5432/fleet"
)


def _pg_up() -> bool:
    import asyncio

    async def _check() -> bool:
        try:
            conn = await asyncpg.connect(FLEET_DSN)
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(_check())


pytestmark = pytest.mark.skipif(
    not _pg_up(), reason="Postgres not reachable — start with `make dev`"
)


def _tool() -> PgReadOnlyTool:
    return PgReadOnlyTool(
        runner=AsyncpgRunner(dsn=FLEET_DSN),
        allowlisted_tables={"fixture_sales", "fixture_orders"},
    )


async def test_live_query_against_fixture_sales_returns_rows() -> None:
    tool = _tool()
    rows = await tool.query("SELECT * FROM fixture_sales")
    assert len(rows) == 500
    assert "amount_usd" in rows[0]


async def test_live_query_on_non_allowlisted_table_never_reaches_db() -> None:
    tool = _tool()
    with pytest.raises(NonAllowlistedTableError):
        await tool.query("SELECT * FROM users")


async def test_set_role_actually_restricts_to_select_even_bypassing_the_tool_guard() -> None:
    """Defense-in-depth: connect exactly as the runner does and confirm the DB
    session itself refuses a write once SET ROLE fleet_readonly has run, not
    just that PgReadOnlyTool's own parser blocks the SQL string. Targets a real
    table (departments), not fixture_sales — that's a generate_series view,
    which Postgres already rejects writes to as structurally non-updatable
    before privileges are even checked, so it wouldn't prove the role boundary."""
    conn = await asyncpg.connect(FLEET_DSN)
    try:
        await conn.execute("SET ROLE fleet_readonly")
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.execute("DELETE FROM departments WHERE id = -1")
    finally:
        await conn.close()

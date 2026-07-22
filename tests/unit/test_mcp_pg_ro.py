"""fleet_mcp.servers.pg_ro: read-only governed-SQL tool (task 5.1, dept scenario
02 Self-Service Analytics).

Enforces the AC from docs/split/department-scenarios/02-self-service-analytics.md:
non-allowlisted table -> refuse + log; DML keywords hard-blocked; auto-LIMIT
1000; 15s timeout; queries run as `fleet_readonly`. The actual DB execution is
injected (a QueryRunner protocol) so this stays unit-testable without a live
Postgres — the live wiring (asyncpg over fleet_readonly) is exercised in
tests/integration.
"""

from __future__ import annotations

import pytest
from fleet_mcp.servers.pg_ro import (
    NonAllowlistedTableError,
    PgReadOnlyTool,
    UnsafeSqlError,
)


class _FakeRunner:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, float]] = []

    async def run(
        self, sql: str, *, timeout: float  # noqa: ASYNC109 — mirrors the real QueryRunner protocol
    ) -> list[dict[str, object]]:
        self.calls.append((sql, timeout))
        return self.rows


def _tool(runner: _FakeRunner) -> PgReadOnlyTool:
    return PgReadOnlyTool(
        runner=runner,
        allowlisted_tables={"fixture_sales", "fixture_orders"},
        row_limit=1000,
        timeout_seconds=15.0,
    )


async def test_allowlisted_query_runs_and_returns_rows() -> None:
    runner = _FakeRunner([{"id": 1, "amount_usd": 100}])
    tool = _tool(runner)
    rows = await tool.query("SELECT * FROM fixture_sales")
    assert rows == [{"id": 1, "amount_usd": 100}]


async def test_query_on_non_allowlisted_table_is_refused_and_logged() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    with pytest.raises(NonAllowlistedTableError):
        await tool.query("SELECT * FROM users_raw")
    assert runner.calls == []  # never reached the DB
    assert tool.refusal_log[-1]["table"] == "users_raw"


async def test_dml_keywords_hard_blocked() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    for statement in [
        "DELETE FROM fixture_sales",
        "UPDATE fixture_sales SET amount_usd = 0",
        "INSERT INTO fixture_sales VALUES (1)",
        "DROP TABLE fixture_sales",
        "TRUNCATE fixture_sales",
        "ALTER TABLE fixture_sales ADD COLUMN x int",
    ]:
        with pytest.raises(UnsafeSqlError):
            await tool.query(statement)
    assert runner.calls == []


async def test_auto_limit_appended_when_missing() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    await tool.query("SELECT * FROM fixture_sales")
    sql, _ = runner.calls[0]
    assert "LIMIT 1000" in sql


async def test_existing_limit_under_cap_is_preserved() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    await tool.query("SELECT * FROM fixture_sales LIMIT 10")
    sql, _ = runner.calls[0]
    assert sql.rstrip().endswith("LIMIT 10")


async def test_existing_limit_over_cap_is_clamped() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    await tool.query("SELECT * FROM fixture_sales LIMIT 50000")
    sql, _ = runner.calls[0]
    assert "LIMIT 1000" in sql
    assert "50000" not in sql


async def test_timeout_seconds_passed_to_runner() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    await tool.query("SELECT * FROM fixture_sales")
    _, timeout = runner.calls[0]
    assert timeout == 15.0


async def test_join_across_two_allowlisted_tables_is_allowed() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    await tool.query(
        "SELECT * FROM fixture_sales s JOIN fixture_orders o ON o.sale_id = s.id"
    )
    assert runner.calls  # reached the DB, not refused


async def test_join_with_one_non_allowlisted_table_is_refused() -> None:
    runner = _FakeRunner([])
    tool = _tool(runner)
    with pytest.raises(NonAllowlistedTableError):
        await tool.query(
            "SELECT * FROM fixture_sales s JOIN users_raw u ON u.id = s.id"
        )
    assert runner.calls == []

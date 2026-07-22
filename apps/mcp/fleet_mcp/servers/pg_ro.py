"""pg_ro MCP tool: governed read-only SQL (task 5.1, dept scenario 02).

Enforces the department-scenario 02 guardrails ahead of ever reaching the DB:
only SELECT statements over an explicit table allowlist, DML/DDL hard-blocked,
auto-LIMIT 1000 (existing LIMIT above the cap is clamped down, never raised),
15s statement timeout. Runs as the `fleet_readonly` Postgres role (migration
0001) so even a bypass of the checks below hits DB-level read-only enforcement
too (defense in depth, same pattern as core.killswitch's execute_tool check).

SQL is parsed with sqlglot rather than regex/string matching — table names and
statement type need real parsing to avoid both false negatives (a DML keyword
hidden in a CTE or subquery slipping past a naive keyword search) and false
positives (a column or alias that happens to contain a blocked substring).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

import sqlglot
from core.errors import GovernedToolRefusal
from sqlglot import exp

_BLOCKED_STATEMENT_TYPES = (
    exp.Delete,
    exp.Update,
    exp.Insert,
    exp.Drop,
    exp.TruncateTable,
    exp.Alter,
    exp.Create,
)


# mypy sees GovernedToolRefusal as Any here: apps/mcp has no fleet-runtime
# workspace dependency declared (only fleet-rag -> fleet-runtime transitively),
# and core/ has no py.typed marker, so this cross-package import is untyped
# from mypy's perspective even though it resolves correctly at runtime (proven
# by tests/unit/test_analytics_service.py's isinstance-based catch). Adding
# py.typed to core/ fixes this in isolation but breaks mypy's module-identity
# resolution when apps/runtime and apps/mcp are type-checked in the same
# invocation (a `Source file found twice` collision) — not worth trading one
# false positive for a different false positive.
class NonAllowlistedTableError(GovernedToolRefusal):  # type: ignore[misc]
    """Query references a table outside the server's allowlist."""


class UnsafeSqlError(GovernedToolRefusal):  # type: ignore[misc]
    """Query is not a plain read (DML/DDL, or otherwise unsafe)."""


class QueryRunner(Protocol):
    async def run(
        self, sql: str, *, timeout: float  # noqa: ASYNC109 — passed straight to asyncpg's own timeout
    ) -> list[dict[str, Any]]: ...


RunnerFactory = Callable[[], Awaitable[QueryRunner]]


def _referenced_tables(parsed: exp.Expression) -> set[str]:
    return {t.name for t in parsed.find_all(exp.Table)}


def _clamp_limit(parsed: exp.Select, row_limit: int) -> exp.Select:
    existing = parsed.args.get("limit")
    if existing is not None:
        try:
            current = int(existing.expression.this)
        except (AttributeError, TypeError, ValueError):
            current = row_limit
        if current > row_limit:
            parsed.set("limit", exp.Limit(expression=exp.Literal.number(row_limit)))
        return parsed
    return parsed.limit(row_limit)


@dataclass
class PgReadOnlyTool:
    runner: QueryRunner
    allowlisted_tables: set[str]
    row_limit: int = 1000
    timeout_seconds: float = 15.0
    refusal_log: list[dict[str, Any]] = field(default_factory=list)

    async def query(self, sql: str) -> list[dict[str, Any]]:
        parsed_statements = sqlglot.parse(sql, read="postgres")
        if len(parsed_statements) != 1 or parsed_statements[0] is None:
            raise UnsafeSqlError("exactly one SELECT statement is required")
        parsed = parsed_statements[0]

        if isinstance(parsed, _BLOCKED_STATEMENT_TYPES) or not isinstance(parsed, exp.Select):
            raise UnsafeSqlError(f"statement type not allowed: {type(parsed).__name__}")

        tables = _referenced_tables(parsed)
        disallowed = tables - self.allowlisted_tables
        if disallowed:
            for table in disallowed:
                self.refusal_log.append({"table": table, "sql": sql})
            raise NonAllowlistedTableError(f"non-allowlisted table(s): {sorted(disallowed)}")

        bounded = _clamp_limit(parsed, self.row_limit)
        return await self.runner.run(bounded.sql(dialect="postgres"), timeout=self.timeout_seconds)

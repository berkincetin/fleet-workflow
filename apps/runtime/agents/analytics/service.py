"""Analytics agent orchestration: NL question -> SQL -> governed execution
(task 5.2, dept scenario 02).

Wires sql_generator.generate_sql() to a governed query tool (structurally
fleet_mcp.servers.pg_ro.PgReadOnlyTool, referenced here only via the
GovernedQueryTool Protocol below — apps/runtime has no fleet-mcp workspace
dependency, since fleet-mcp -> fleet-rag -> fleet-runtime already, and a
runtime -> mcp edge would create a cycle; the caller in apps/api, which does
depend on both, passes the real PgReadOnlyTool in). This module owns none of
the allowlist/DML/timeout guardrails itself — those stay in pg_ro, so
Analytics gets them for free and can never drift from what pg_ro enforces
for any other caller. Refusals are recognized via core.errors.GovernedToolRefusal
(a real isinstance check pg_ro's exceptions subclass), not by exception-name
string matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from agents.analytics.semantic_layer import SemanticLayer
from agents.analytics.sql_generator import ClarificationNeeded, ReasoningClient, generate_sql
from core.errors import GovernedToolRefusal


class AnalyticsClarification(Exception):
    """The question was ambiguous; carries the one clarifying question to ask."""


class AnalyticsRefusal(Exception):
    """The generated SQL touched a non-allowlisted table; refused and logged."""


class GovernedQueryTool(Protocol):
    async def query(self, sql: str) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class AnalyticsResult:
    sql: str
    rows: list[dict[str, Any]]


async def ask_analytics(
    *,
    question: str,
    semantic_layer: SemanticLayer,
    llm_client: ReasoningClient,
    pg_tool: GovernedQueryTool,
    **meta: Any,
) -> AnalyticsResult:
    try:
        sql = await generate_sql(
            question=question, semantic_layer=semantic_layer, llm_client=llm_client, **meta
        )
    except ClarificationNeeded as exc:
        raise AnalyticsClarification(str(exc)) from exc

    try:
        rows = await pg_tool.query(sql)
    except GovernedToolRefusal as exc:
        raise AnalyticsRefusal(str(exc)) from exc

    return AnalyticsResult(sql=sql, rows=rows)

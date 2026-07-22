"""agents.analytics.service: orchestrates NL question -> SQL -> governed
execution -> {sql, rows} (task 5.2).

Wires sql_generator.generate_sql() to fleet_mcp.servers.pg_ro.PgReadOnlyTool
— the same governed-SQL tool 5.1 built, so the Analytics agent gets the
allowlist/DML-block/auto-LIMIT/timeout guardrails for free rather than
re-implementing them. AC: business question -> table + SQL shown; refused +
logged query on a non-allowlisted table; ambiguous question asks one
clarifying question.
"""

from __future__ import annotations

import pytest
from agents.analytics.semantic_layer import DEFAULT_SEMANTIC_LAYER
from agents.analytics.service import AnalyticsClarification, AnalyticsRefusal, ask_analytics
from fleet_mcp.servers.pg_ro import PgReadOnlyTool


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content

    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        class _Resp:
            content = self.content

        return _Resp()


class _FakeRunner:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    async def run(self, sql: str, *, timeout: float) -> list[dict[str, object]]:  # noqa: ASYNC109
        return self.rows


def _pg_tool(rows: list[dict[str, object]] | None = None) -> PgReadOnlyTool:
    return PgReadOnlyTool(
        runner=_FakeRunner(rows or []),
        allowlisted_tables=DEFAULT_SEMANTIC_LAYER.allowlisted_tables(),
    )


async def test_clear_question_returns_sql_and_rows() -> None:
    llm = _FakeLLM('{"sql": "SELECT region, amount_usd FROM fixture_sales"}')
    pg_tool = _pg_tool(rows=[{"region": "TR", "amount_usd": 100}])

    result = await ask_analytics(
        question="show sales by region",
        semantic_layer=DEFAULT_SEMANTIC_LAYER,
        llm_client=llm,
        pg_tool=pg_tool,
    )

    assert "fixture_sales" in result.sql
    assert result.rows == [{"region": "TR", "amount_usd": 100}]


async def test_ambiguous_question_raises_clarification() -> None:
    llm = _FakeLLM('{"clarify": "Which region?"}')
    pg_tool = _pg_tool()

    with pytest.raises(AnalyticsClarification) as exc_info:
        await ask_analytics(
            question="show sales", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm,
            pg_tool=pg_tool,
        )
    assert "Which region?" in str(exc_info.value)


async def test_non_allowlisted_table_is_refused_and_logged() -> None:
    llm = _FakeLLM('{"sql": "SELECT * FROM users_raw"}')
    pg_tool = _pg_tool()

    with pytest.raises(AnalyticsRefusal):
        await ask_analytics(
            question="show me raw users", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm,
            pg_tool=pg_tool,
        )
    assert pg_tool.refusal_log[-1]["table"] == "users_raw"


async def test_sensitivity_in_meta_does_not_collide_with_generate_sql_default() -> None:
    """Caught live (test_chat_analytics_live.py): chat.py passes
    sensitivity=agent.sensitivity through **meta; generate_sql must accept it
    as its own named parameter, not double-pass sensitivity to
    llm_client.reasoning()."""
    llm = _FakeLLM('{"sql": "SELECT 1 FROM fixture_sales"}')
    pg_tool = _pg_tool(rows=[{"x": 1}])

    result = await ask_analytics(
        question="q", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm, pg_tool=pg_tool,
        sensitivity="internal", agent_id="1", trace_id="t1",
    )
    assert result.sql == "SELECT 1 FROM fixture_sales"


async def test_generated_sql_is_always_surfaced_alongside_rows() -> None:
    llm = _FakeLLM('{"sql": "SELECT id FROM fixture_orders"}')
    pg_tool = _pg_tool(rows=[{"id": 1}])

    result = await ask_analytics(
        question="list order ids", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm,
        pg_tool=pg_tool,
    )
    assert result.sql == "SELECT id FROM fixture_orders"

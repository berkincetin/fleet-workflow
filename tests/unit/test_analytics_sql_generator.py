"""agents.analytics.sql_generator: NL question -> SQL, or a clarifying
question (task 5.2, dept scenario 02).

The LLM call is injected (a Generator protocol) so this is testable without
network; the real wiring uses LLMClient.reasoning() (SQL gen is the
department scenario's designated reasoning-tier call-site). The model is
prompted to emit one of two JSON shapes — {"sql": "..."} or
{"clarify": "..."} — and generate_sql() parses whichever came back rather
than guessing when the question is ambiguous, per the AC:
"ambiguous question -> asks one clarifying question instead of guessing."
"""

from __future__ import annotations

import pytest
from agents.analytics.semantic_layer import DEFAULT_SEMANTIC_LAYER
from agents.analytics.sql_generator import ClarificationNeeded, generate_sql


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[list[dict[str, object]]] = []

    async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
        self.calls.append(messages)

        class _Resp:
            content = self.content

        return _Resp()


async def test_generate_sql_returns_sql_for_clear_question() -> None:
    llm = _FakeLLM('{"sql": "SELECT region, SUM(amount_usd) FROM fixture_sales GROUP BY region"}')
    sql = await generate_sql(
        question="total sales by region",
        semantic_layer=DEFAULT_SEMANTIC_LAYER,
        llm_client=llm,
    )
    assert sql.startswith("SELECT")
    assert "fixture_sales" in sql


async def test_generate_sql_raises_clarification_needed_for_ambiguous_question() -> None:
    llm = _FakeLLM('{"clarify": "Which time period do you mean by \\"recent\\"?"}')
    with pytest.raises(ClarificationNeeded) as exc_info:
        await generate_sql(
            question="how are recent sales", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm
        )
    assert "time period" in str(exc_info.value)


async def test_generate_sql_prompt_includes_semantic_layer_glossary() -> None:
    llm = _FakeLLM('{"sql": "SELECT 1"}')
    await generate_sql(
        question="anything", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm
    )
    system_content = llm.calls[0][0]["content"]
    assert "fixture_sales" in system_content
    assert "fixture_orders" in system_content


async def test_generate_sql_uses_reasoning_tier_not_utility() -> None:
    class _TierCheckLLM:
        def __init__(self) -> None:
            self.reasoning_called = False

        async def reasoning(self, messages: list[dict[str, object]], **kwargs: object) -> object:
            self.reasoning_called = True

            class _Resp:
                content = '{"sql": "SELECT 1"}'

            return _Resp()

    llm = _TierCheckLLM()
    await generate_sql(question="x", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm)
    assert llm.reasoning_called is True


async def test_generate_sql_raises_on_malformed_llm_response() -> None:
    llm = _FakeLLM("not json at all")
    with pytest.raises(ValueError):
        await generate_sql(question="x", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm)


async def test_generate_sql_strips_markdown_code_fence() -> None:
    """Caught live (make eval AGENT=analytics): some models wrap the JSON in a
    ```json ... ``` fence despite being told not to."""
    llm = _FakeLLM('```json\n{"sql": "SELECT 1 FROM fixture_sales"}\n```')
    sql = await generate_sql(
        question="anything", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm
    )
    assert sql == "SELECT 1 FROM fixture_sales"


async def test_generate_sql_strips_plain_code_fence_without_json_tag() -> None:
    llm = _FakeLLM('```\n{"clarify": "Which region?"}\n```')
    with pytest.raises(ClarificationNeeded):
        await generate_sql(
            question="anything", semantic_layer=DEFAULT_SEMANTIC_LAYER, llm_client=llm
        )

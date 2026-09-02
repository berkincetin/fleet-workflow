"""agents.insights_publisher.graph + grounding — numbers-match guardrail gates
the HITL approval (task 11.3, dept scenario 08).

Proves: a draft whose numbers all match the data reaches the write:external
HITL interrupt (approve -> publish; reject -> no publish); a draft with an
invented number is blocked BEFORE hitl (a human never approves an invented
stat); the numbers-match guardrail's extraction/normalisation handles TR/EN
number formats; paused agent short-circuits.
"""

from __future__ import annotations

import json
from typing import Any

from agents.insights_publisher.graph import build_insights_publisher_graph
from agents.insights_publisher.grounding import check_numbers_grounded, extract_numbers
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class _FakeReasoning:
    def __init__(self, draft: dict[str, str]) -> None:
        self._content = json.dumps(draft, ensure_ascii=False)

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        class _Resp:
            content = self._content

        return _Resp()


class _FakeData:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    async def monthly_rows(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeBrand:
    async def guidance(self) -> str:
        return "Sıcak, güven veren, sade bir dil kullan."


class _FakePublisher:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def publish(self, *, report: str, social: str) -> dict[str, Any]:
        self.calls.append({"report": report, "social": social})
        return {"cms_id": "POST-1", "status": "published"}


_ROWS = [{"segment": "sedan", "avg_price": 500000}, {"segment": "suv", "avg_price": 800000}]


def _graph(reasoning: _FakeReasoning, publisher: _FakePublisher, rows=_ROWS) -> Any:
    return build_insights_publisher_graph(
        llm_client=reasoning,
        index_data=_FakeData(rows),
        brand_voice=_FakeBrand(),
        publisher=publisher,
        checkpointer=InMemorySaver(),
    )


async def test_grounded_draft_reaches_hitl_then_publishes_on_approve() -> None:
    reasoning = _FakeReasoning(
        {"report": "Sedan ortalaması 500000 TL.", "social": "SUV 800000 TL!"}
    )
    publisher = _FakePublisher()
    graph = _graph(reasoning, publisher)
    cfg = {"configurable": {"thread_id": "1"}}
    result = await graph.ainvoke({}, cfg)
    assert "__interrupt__" in result  # write:external -> approval
    assert result["__interrupt__"][0].value["risk_class"] == "write:external"
    # the data is attached to the approval item (grounding evidence)
    assert result["__interrupt__"][0].value["grounded_against"] == _ROWS
    resumed = await graph.ainvoke(Command(resume={"approved": True}), cfg)
    assert resumed["published"]["status"] == "published"
    assert publisher.calls  # published only after approval


async def test_reject_does_not_publish() -> None:
    reasoning = _FakeReasoning({"report": "Sedan 500000 TL.", "social": "SUV 800000 TL."})
    publisher = _FakePublisher()
    graph = _graph(reasoning, publisher)
    cfg = {"configurable": {"thread_id": "2"}}
    await graph.ainvoke({}, cfg)
    resumed = await graph.ainvoke(Command(resume={"approved": False}), cfg)
    assert resumed.get("rejected") is True
    assert publisher.calls == []


async def test_invented_number_is_blocked_before_hitl() -> None:
    # 999999 appears nowhere in the data → ungrounded → never reaches approval.
    reasoning = _FakeReasoning(
        {"report": "Sedan 500000 TL, artış %999999.", "social": "SUV 800000 TL."}
    )
    publisher = _FakePublisher()
    graph = _graph(reasoning, publisher)
    result = await graph.ainvoke({}, {"configurable": {"thread_id": "3"}})
    assert "__interrupt__" not in result  # no human ever asked to approve it
    assert result["grounded"] is False
    assert 999999.0 in result["unmatched_numbers"]
    assert publisher.calls == []


async def test_paused_agent_short_circuits() -> None:
    class _Paused:
        async def is_agent_paused(self, name: str) -> bool:
            return True

        async def blocks_tool(self, *, risk_class: str) -> bool:
            return False

    reasoning = _FakeReasoning({"report": "x", "social": "y"})
    publisher = _FakePublisher()
    graph = build_insights_publisher_graph(
        llm_client=reasoning, index_data=_FakeData(_ROWS), brand_voice=_FakeBrand(),
        publisher=publisher, checkpointer=InMemorySaver(), killswitch=_Paused(),
    )
    result = await graph.ainvoke({}, {"configurable": {"thread_id": "4"}})
    assert result.get("paused") is True
    assert publisher.calls == []


# --- grounding guardrail unit checks -----------------------------------------


def test_extract_numbers_handles_tr_and_en_formats() -> None:
    nums = extract_numbers("Fiyat 1.250.000 TL, artış %12,5 ve 500000 adet")
    assert 1250000.0 in nums
    assert 12.5 in nums
    assert 500000.0 in nums


def test_check_numbers_grounded_passes_when_all_match() -> None:
    res = check_numbers_grounded(
        draft_text="Ortalama 500000 TL, en yüksek 800000 TL.",
        data_rows=[{"a": 500000}, {"b": 800000}],
    )
    assert res.grounded is True


def test_check_numbers_grounded_flags_invented_value() -> None:
    res = check_numbers_grounded(
        draft_text="Ortalama 500000 TL ama büyüme %42.",
        data_rows=[{"a": 500000}, {"b": 800000}],
    )
    assert res.grounded is False
    assert 42.0 in res.unmatched

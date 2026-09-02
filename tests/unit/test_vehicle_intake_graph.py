"""agents.vehicle_intake.graph — OCR -> redact -> extract -> comparables -> band
(task 11.2, dept scenario 07).

Proves: a complete report yields a brief + a band containing the comparables'
median; a missing/unusable report is marked incomplete with NO band and NO
invented values; the OCR text is PII-redacted before the reasoning call
(redaction_applied); no write tool / no interrupt exists (advisory only); paused
agent short-circuits.
"""

from __future__ import annotations

import json
from typing import Any

from agents.vehicle_intake.graph import build_vehicle_intake_graph
from langgraph.checkpoint.memory import InMemorySaver


class _FakeOcr:
    def __init__(self, text: str) -> None:
        self.text = text

    async def extract_text(self, image_base64: str) -> dict[str, Any]:
        return {"text": self.text, "source": "tesseract"}


class _FakeReasoning:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict[str, Any]] = []

    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        self.calls.append({"messages": messages, **kwargs})

        class _Resp:
            content = self.content

        return _Resp()


class _FakeComparables:
    def __init__(self, prices: list[float]) -> None:
        self._prices = prices

    async def top_prices(self, *, segment: str, limit: int = 5) -> list[float]:
        return self._prices[:limit]


def _graph(ocr: _FakeOcr, reasoning: _FakeReasoning, comps: _FakeComparables) -> Any:
    return build_vehicle_intake_graph(
        llm_client=reasoning, ocr=ocr, comparables=comps, checkpointer=InMemorySaver()
    )


async def test_complete_report_yields_brief_and_band_containing_median() -> None:
    ocr = _FakeOcr("Sasi No: WVWZZZ1JZ3W386752\nKM: 120000\nHasar: on tampon")
    reasoning = _FakeReasoning(
        json.dumps({"chassis": "WVWZZZ1JZ3W386752", "km": 120000, "damage": ["on tampon"]})
    )
    comps = _FakeComparables([480000, 500000, 520000, 460000, 540000])
    result = await _graph(ocr, reasoning, comps).ainvoke(
        {"image_base64": "eA==", "segment": "sedan-2018"}, {"configurable": {"thread_id": "1"}}
    )
    assert result["incomplete"] is False
    assert result["brief"]["chassis"] == "WVWZZZ1JZ3W386752"
    assert result["brief"]["km"] == 120000
    band = result["price_band"]
    assert band is not None
    # Band must contain the median of the comparables (500000).
    assert band["low"] <= 500000 <= band["high"]


async def test_missing_report_is_incomplete_with_no_band_no_invented_values() -> None:
    ocr = _FakeOcr("this page is blank / not an expertise report")
    reasoning = _FakeReasoning(json.dumps({"chassis": None, "km": None, "damage": []}))
    comps = _FakeComparables([480000, 500000, 520000])
    result = await _graph(ocr, reasoning, comps).ainvoke(
        {"image_base64": "eA==", "segment": "sedan-2018"}, {"configurable": {"thread_id": "2"}}
    )
    assert result["incomplete"] is True
    # No band invented for an incomplete report; comparables never fetched.
    assert result.get("price_band") is None
    assert result["brief"]["chassis"] is None and result["brief"]["km"] is None


async def test_ocr_text_is_redacted_before_reasoning() -> None:
    # OCR text carries owner PII; the reasoning call must receive the masked form.
    ocr = _FakeOcr("Sahibi: 05551234567 Sasi: ABC123 KM: 90000")
    reasoning = _FakeReasoning(json.dumps({"chassis": "ABC123", "km": 90000, "damage": []}))
    comps = _FakeComparables([300000, 320000])
    result = await _graph(ocr, reasoning, comps).ainvoke(
        {"image_base64": "eA==", "segment": "hatchback-2019"}, {"configurable": {"thread_id": "3"}}
    )
    sent = reasoning.calls[0]["messages"][1]["content"]
    assert "05551234567" not in sent  # phone masked
    assert "[TR_PHONE]" in sent
    assert reasoning.calls[0].get("redacted") is True  # routing downgrade signalled
    assert result["brief"]["redaction_applied"] is True


async def test_no_write_tool_or_interrupt_in_result() -> None:
    ocr = _FakeOcr("Sasi: X km: 1")
    reasoning = _FakeReasoning(json.dumps({"chassis": "X", "km": 1, "damage": []}))
    comps = _FakeComparables([100000])
    result = await _graph(ocr, reasoning, comps).ainvoke(
        {"image_base64": "eA==", "segment": "s"}, {"configurable": {"thread_id": "4"}}
    )
    assert "__interrupt__" not in result  # advisory: never pauses for approval


async def test_paused_agent_short_circuits() -> None:
    class _Paused:
        async def is_agent_paused(self, name: str) -> bool:
            return True

        async def blocks_tool(self, *, risk_class: str) -> bool:
            return False

    ocr = _FakeOcr("x")
    reasoning = _FakeReasoning("{}")
    comps = _FakeComparables([1])
    graph = build_vehicle_intake_graph(
        llm_client=reasoning, ocr=ocr, comparables=comps,
        checkpointer=InMemorySaver(), killswitch=_Paused(),
    )
    result = await graph.ainvoke(
        {"image_base64": "eA==", "segment": "s"}, {"configurable": {"thread_id": "5"}}
    )
    assert result.get("paused") is True
    assert reasoning.calls == []

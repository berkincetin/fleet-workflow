"""agents.listing_quality.graph — vision check -> flag-only routing (task 11.1,
dept scenario 06).

Proves the flag-only guardrail structurally: the graph's only mutating tool is
listings.flag, a clean listing reaches `end` without flagging, a flagged one
calls flag with the machine-readable codes, an invented code is dropped by the
checker's closed vocabulary, and a paused agent short-circuits.
"""

from __future__ import annotations

import json
from typing import Any

from agents.listing_quality.graph import build_listing_quality_graph
from langgraph.checkpoint.memory import InMemorySaver


class _FakeVision:
    """Returns a canned JSON verdict from the utility (vision) call."""

    def __init__(self, verdict: dict[str, Any]) -> None:
        self._content = json.dumps(verdict)
        self.calls: list[dict[str, Any]] = []

    async def utility(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        self.calls.append({"messages": messages, **kwargs})

        class _Resp:
            content = self._content

        return _Resp()


class _FakePriceIndex:
    def __init__(self, band: dict[str, Any] | None) -> None:
        self._band = band

    async def reference_band(self, *, segment: str) -> dict[str, Any] | None:
        return self._band


class _FakeFlag:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def flag(
        self, *, listing_id: str, codes: list[str], reasons: list[str]
    ) -> dict[str, Any]:
        self.calls.append({"listing_id": listing_id, "codes": codes, "reasons": reasons})
        return {"flag_id": "FLAG-test", "status": "queued_for_review"}


_BAND = {"low": 400000, "high": 600000, "median": 500000, "currency": "TRY"}


def _graph(vision: _FakeVision, flag: _FakeFlag, band: dict[str, Any] | None = _BAND) -> Any:
    return build_listing_quality_graph(
        vision_client=vision,
        price_index=_FakePriceIndex(band),
        listings_flag=flag,
        checkpointer=InMemorySaver(),
    )


def _listing(**over: Any) -> dict[str, Any]:
    base = {
        "listing_id": "L-0001",
        "image_base64": "eA==",
        "description": "sedan 2018, clean",
        "price": 500000.0,
        "currency": "TRY",
        "segment": "sedan-2018",
    }
    base.update(over)
    return base


async def test_clean_listing_is_not_flagged() -> None:
    vision = _FakeVision({"flags": []})
    flag = _FakeFlag()
    result = await _graph(vision, flag).ainvoke(_listing(), {"configurable": {"thread_id": "1"}})
    assert result["verdict"]["clean"] is True
    assert flag.calls == []  # flag-only: nothing queued for a clean listing


async def test_flagged_listing_calls_flag_with_codes() -> None:
    vision = _FakeVision(
        {"flags": [{"code": "price_anomaly", "reason": "way above band"}]}
    )
    flag = _FakeFlag()
    result = await _graph(vision, flag).ainvoke(
        _listing(price=2_000_000.0), {"configurable": {"thread_id": "2"}}
    )
    assert result["flagged"] is True
    assert flag.calls and flag.calls[0]["codes"] == ["price_anomaly"]


async def test_invented_code_is_dropped_by_closed_vocabulary() -> None:
    vision = _FakeVision(
        {"flags": [{"code": "unpublish_now", "reason": "model tried a new action"}]}
    )
    flag = _FakeFlag()
    result = await _graph(vision, flag).ainvoke(_listing(), {"configurable": {"thread_id": "3"}})
    # The invented code is not in REASON_CODES → dropped → treated as clean.
    assert result["verdict"]["clean"] is True
    assert flag.calls == []


async def test_multiple_flags_all_forwarded() -> None:
    vision = _FakeVision(
        {
            "flags": [
                {"code": "photo_description_mismatch", "reason": "blue not red"},
                {"code": "blurred_plate_missing", "reason": "plate readable"},
            ]
        }
    )
    flag = _FakeFlag()
    await _graph(vision, flag).ainvoke(_listing(), {"configurable": {"thread_id": "4"}})
    assert set(flag.calls[0]["codes"]) == {
        "photo_description_mismatch",
        "blurred_plate_missing",
    }


async def test_paused_agent_short_circuits_before_vision() -> None:
    class _Paused:
        async def is_agent_paused(self, name: str) -> bool:
            return True

        async def blocks_tool(self, *, risk_class: str) -> bool:
            return False

    vision = _FakeVision({"flags": []})
    flag = _FakeFlag()
    graph = build_listing_quality_graph(
        vision_client=vision,
        price_index=_FakePriceIndex(_BAND),
        listings_flag=flag,
        checkpointer=InMemorySaver(),
        killswitch=_Paused(),
    )
    result = await graph.ainvoke(_listing(), {"configurable": {"thread_id": "5"}})
    assert result.get("paused") is True
    assert vision.calls == []  # never reached the vision call
    assert flag.calls == []

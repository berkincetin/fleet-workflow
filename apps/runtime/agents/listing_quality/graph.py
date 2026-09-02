"""Listing Quality agent graph (task 11.1, dept scenario 06).

Node order: killswitch_gate -> fetch_band (pg_ro price-index reference band for
the listing's segment, `read`) -> vision_check (utility vision call ->
ListingVerdict) -> [clean: pass] / [flagged: flag]. The `flag` node calls
`listings.flag` (write:internal) with the machine-readable reason codes.

Flag-only guardrail (dept scenario 06): the agent can NEVER unpublish or reject
a listing. The only mutating tool it holds is `listings.flag`, which routes the
listing into the human review queue; there is no unpublish path in the graph at
all. `listings.flag` is write:internal (supervised), not write:external, so it
does not go through the HITL approval interrupt — but the guardrail is
structural: no other write tool is wired.

Tool objects are referenced via local Protocols only; apps/runtime has no
fleet-mcp dependency (same boundary as invoice/hr/dev agents). The caller in
apps/api passes the real fleet_mcp instances in.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from agents.listing_quality.checker import (
    CheckParseError,
    ListingVerdict,
    VisionClient,
    check_listing,
)
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph


class PriceIndexLike(Protocol):
    async def reference_band(self, *, segment: str) -> dict[str, Any] | None: ...


class ListingsFlagLike(Protocol):
    async def flag(
        self, *, listing_id: str, codes: list[str], reasons: list[str]
    ) -> dict[str, Any]: ...


class ListingQualityState(TypedDict, total=False):
    listing_id: str
    image_base64: str
    description: str
    price: float
    currency: str
    segment: str
    reference_band: dict[str, Any] | None
    verdict: dict[str, Any]
    flagged: bool
    flag_result: dict[str, Any]
    blocked_reason: str | None
    paused: bool


_LISTINGS_FLAG_RISK_CLASS = "write:internal"


def build_listing_quality_graph(
    *,
    vision_client: VisionClient,
    price_index: PriceIndexLike,
    listings_flag: ListingsFlagLike,
    checkpointer: Any,
    killswitch: KillSwitch | None = None,
    agent_name: str = "listing_quality",
) -> Any:
    async def killswitch_gate(state: ListingQualityState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: ListingQualityState) -> str:
        return END if state.get("paused") else "fetch_band"

    async def fetch_band(state: ListingQualityState) -> dict[str, Any]:
        band = await price_index.reference_band(segment=state.get("segment", ""))
        return {"reference_band": band}

    async def vision_check(state: ListingQualityState) -> dict[str, Any]:
        try:
            verdict: ListingVerdict = await check_listing(
                image_base64=state["image_base64"],
                description=state["description"],
                price=state["price"],
                currency=state.get("currency", "TRY"),
                reference_band=state.get("reference_band"),
                vision_client=vision_client,
            )
        except CheckParseError as exc:
            return {"blocked_reason": f"vision check failed: {exc}"}
        return {
            "verdict": {
                "flags": [{"code": f.code, "reason": f.reason} for f in verdict.flags],
                "clean": verdict.is_clean,
            },
            "flagged": not verdict.is_clean,
        }

    def route_after_check(state: ListingQualityState) -> str:
        if state.get("blocked_reason"):
            return "end"
        return "flag" if state.get("flagged") else "end"

    async def flag(state: ListingQualityState) -> dict[str, Any]:
        flags = state["verdict"]["flags"]
        result = await listings_flag.flag(
            listing_id=state["listing_id"],
            codes=[f["code"] for f in flags],
            reasons=[f["reason"] for f in flags],
        )
        return {"flag_result": result}

    async def end_node(state: ListingQualityState) -> dict[str, Any]:
        return {}

    graph = StateGraph(ListingQualityState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("fetch_band", fetch_band)
    graph.add_node("vision_check", vision_check)
    graph.add_node("flag", flag)
    graph.add_node("end", end_node)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate", route_after_killswitch, {END: END, "fetch_band": "fetch_band"}
    )
    graph.add_edge("fetch_band", "vision_check")
    graph.add_conditional_edges(
        "vision_check", route_after_check, {"flag": "flag", "end": "end"}
    )
    graph.add_edge("flag", "end")
    graph.add_edge("end", END)

    return graph.compile(checkpointer=checkpointer)

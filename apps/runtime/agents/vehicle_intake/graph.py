"""Vehicle Intake agent graph (task 11.2, dept scenario 07).

Node order: killswitch_gate -> ocr (LOCAL OCR of the expertise PDF, owner PII)
-> extract (redact the OCR text, then cloud reasoning on the redacted brief ->
VehicleBrief) -> comparables (pg_ro top-5 prices for the segment) ->
suggest_band (deterministic price band containing the comparables' median) ->
END. Advisory only: NO write tools, NO HITL interrupt — the human makes the
offer (dept scenario 07 rollout "assist permanently").

Missing-report guardrail: if extraction returns `incomplete` (no chassis/km),
the brief is emitted marked incomplete with no comparables/band invented.

Tools referenced via local Protocols; apps/runtime has no fleet-mcp dependency.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from agents.vehicle_intake.extractor import (
    ExtractionParseError,
    ReasoningClient,
    VehicleBrief,
    extract_vehicle_brief,
)
from agents.vehicle_intake.price_band import ComparablesLike, suggest_band
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph


class OcrLike(Protocol):
    async def extract_text(self, image_base64: str) -> dict[str, Any]: ...


class VehicleIntakeState(TypedDict, total=False):
    image_base64: str
    segment: str
    ocr_text: str
    brief: dict[str, Any]
    comparables: list[float]
    price_band: dict[str, Any] | None
    incomplete: bool
    blocked_reason: str | None
    paused: bool


def build_vehicle_intake_graph(
    *,
    llm_client: ReasoningClient,
    ocr: OcrLike,
    comparables: ComparablesLike,
    checkpointer: Any,
    killswitch: KillSwitch | None = None,
    agent_name: str = "vehicle_intake",
) -> Any:
    async def killswitch_gate(state: VehicleIntakeState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: VehicleIntakeState) -> str:
        return END if state.get("paused") else "ocr"

    async def ocr_node(state: VehicleIntakeState) -> dict[str, Any]:
        # LOCAL OCR — the expertise report carries owner PII (TRD §8), so the raw
        # image never reaches the cloud vision model.
        result = await ocr.extract_text(image_base64=state["image_base64"])
        return {"ocr_text": result["text"]}

    async def extract(state: VehicleIntakeState) -> dict[str, Any]:
        try:
            brief: VehicleBrief = await extract_vehicle_brief(
                ocr_text=state["ocr_text"], llm_client=llm_client
            )
        except ExtractionParseError as exc:
            return {"blocked_reason": f"vehicle extraction failed: {exc}", "incomplete": True}
        return {
            "brief": {
                "chassis": brief.chassis, "km": brief.km, "damage": brief.damage,
                "redaction_applied": brief.redaction_applied,
            },
            "incomplete": brief.incomplete,
        }

    def route_after_extract(state: VehicleIntakeState) -> str:
        # An incomplete/blocked report skips comparables + band — no invented values.
        if state.get("blocked_reason") or state.get("incomplete"):
            return "end"
        return "comparables"

    async def comparables_node(state: VehicleIntakeState) -> dict[str, Any]:
        prices = await comparables.top_prices(segment=state.get("segment", ""), limit=5)
        return {"comparables": prices}

    async def suggest_band_node(state: VehicleIntakeState) -> dict[str, Any]:
        band = suggest_band(state.get("comparables", []))
        return {
            "price_band": (
                {
                    "low": band.low, "high": band.high, "median": band.median,
                    "currency": band.currency, "comparable_count": band.comparable_count,
                }
                if band is not None
                else None
            )
        }

    async def end_node(state: VehicleIntakeState) -> dict[str, Any]:
        return {}

    graph = StateGraph(VehicleIntakeState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("ocr", ocr_node)
    graph.add_node("extract", extract)
    graph.add_node("comparables", comparables_node)
    graph.add_node("suggest_band", suggest_band_node)
    graph.add_node("end", end_node)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate", route_after_killswitch, {END: END, "ocr": "ocr"}
    )
    graph.add_edge("ocr", "extract")
    graph.add_conditional_edges(
        "extract", route_after_extract, {"comparables": "comparables", "end": "end"}
    )
    graph.add_edge("comparables", "suggest_band")
    graph.add_edge("suggest_band", "end")
    graph.add_edge("end", END)

    return graph.compile(checkpointer=checkpointer)

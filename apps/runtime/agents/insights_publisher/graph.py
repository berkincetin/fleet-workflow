"""Insights Publisher agent graph (task 11.3, dept scenario 08).

Node order: killswitch_gate -> pull_data (pg_ro index views, read) ->
retrieve_brand (mkt-brand KB brand-voice text) -> draft (reasoning: report +
social in brand voice) -> grounding (numbers-match: every number in the draft
must match a data value) -> [ungrounded: blocked, no publish] / [grounded:
hitl] -> hitl (interrupt carrying the draft + the data it was grounded against;
cms.publish + social.post are write:external, approval-gated forever for public
content) -> [approved: publish] / [rejected: end].

The grounding guardrail gates the approval item itself: an ungrounded draft
never reaches HITL, so a human is never asked to approve content with an
invented statistic (dept scenario 08: "every numeric claim must match a query
result attached to the approval item").
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from agents.insights_publisher.drafter import (
    Draft,
    DraftParseError,
    ReasoningClient,
    draft_report,
)
from agents.insights_publisher.grounding import check_numbers_grounded
from core.hitl import requires_approval
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt


class IndexDataLike(Protocol):
    async def monthly_rows(self) -> list[dict[str, Any]]: ...


class BrandVoiceLike(Protocol):
    async def guidance(self) -> str: ...


class PublisherLike(Protocol):
    async def publish(self, *, report: str, social: str) -> dict[str, Any]: ...


class InsightsPublisherState(TypedDict, total=False):
    data_rows: list[dict[str, Any]]
    brand_voice: str
    draft: dict[str, str]
    grounded: bool
    unmatched_numbers: list[float]
    blocked_reason: str | None
    rejected: bool
    published: dict[str, Any]
    paused: bool


_PUBLISH_RISK_CLASS = "write:external"


def build_insights_publisher_graph(
    *,
    llm_client: ReasoningClient,
    index_data: IndexDataLike,
    brand_voice: BrandVoiceLike,
    publisher: PublisherLike,
    checkpointer: Any,
    killswitch: KillSwitch | None = None,
    agent_name: str = "insights_publisher",
) -> Any:
    async def killswitch_gate(state: InsightsPublisherState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: InsightsPublisherState) -> str:
        return END if state.get("paused") else "pull_data"

    async def pull_data(state: InsightsPublisherState) -> dict[str, Any]:
        return {"data_rows": await index_data.monthly_rows()}

    async def retrieve_brand(state: InsightsPublisherState) -> dict[str, Any]:
        return {"brand_voice": await brand_voice.guidance()}

    async def draft(state: InsightsPublisherState) -> dict[str, Any]:
        try:
            result: Draft = await draft_report(
                data_rows=state["data_rows"],
                brand_voice=state.get("brand_voice", ""),
                llm_client=llm_client,
            )
        except DraftParseError as exc:
            return {"blocked_reason": f"draft failed: {exc}"}
        return {"draft": {"report": result.report, "social": result.social}}

    def route_after_draft(state: InsightsPublisherState) -> str:
        return "end" if state.get("blocked_reason") else "grounding"

    async def grounding(state: InsightsPublisherState) -> dict[str, Any]:
        d = state["draft"]
        combined = f"{d['report']}\n{d['social']}"
        result = check_numbers_grounded(
            draft_text=combined, data_rows=state["data_rows"]
        )
        if not result.grounded:
            return {
                "grounded": False,
                "unmatched_numbers": result.unmatched,
                "blocked_reason": (
                    f"ungrounded numbers in draft: {result.unmatched} "
                    "(not found in the query results)"
                ),
            }
        return {"grounded": True, "unmatched_numbers": []}

    def route_after_grounding(state: InsightsPublisherState) -> str:
        # An ungrounded draft never reaches HITL — no human approves invented stats.
        return "hitl" if state.get("grounded") else "end"

    async def hitl(state: InsightsPublisherState) -> dict[str, Any]:
        assert requires_approval(
            risk_class=_PUBLISH_RISK_CLASS, eval_pass_rate=0.0, autonomy_enabled=False
        )
        decision = interrupt(
            {
                "tool": "cms.publish+social.post",
                "risk_class": _PUBLISH_RISK_CLASS,
                "args": state["draft"],
                # The data the numbers were grounded against, attached to the
                # approval item (dept scenario 08 requirement).
                "grounded_against": state["data_rows"],
            }
        )
        if not decision.get("approved"):
            return {"rejected": True}
        return {}

    def route_after_hitl(state: InsightsPublisherState) -> str:
        return "end" if state.get("rejected") else "publish"

    async def publish(state: InsightsPublisherState) -> dict[str, Any]:
        d = state["draft"]
        result = await publisher.publish(report=d["report"], social=d["social"])
        return {"published": result}

    async def end_node(state: InsightsPublisherState) -> dict[str, Any]:
        return {}

    graph = StateGraph(InsightsPublisherState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("pull_data", pull_data)
    graph.add_node("retrieve_brand", retrieve_brand)
    graph.add_node("draft", draft)
    graph.add_node("grounding", grounding)
    graph.add_node("hitl", hitl)
    graph.add_node("publish", publish)
    graph.add_node("end", end_node)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate", route_after_killswitch, {END: END, "pull_data": "pull_data"}
    )
    graph.add_edge("pull_data", "retrieve_brand")
    graph.add_edge("retrieve_brand", "draft")
    graph.add_conditional_edges(
        "draft", route_after_draft, {"grounding": "grounding", "end": "end"}
    )
    graph.add_conditional_edges(
        "grounding", route_after_grounding, {"hitl": "hitl", "end": "end"}
    )
    graph.add_conditional_edges(
        "hitl", route_after_hitl, {"publish": "publish", "end": "end"}
    )
    graph.add_edge("publish", "end")
    graph.add_edge("end", END)

    return graph.compile(checkpointer=checkpointer)

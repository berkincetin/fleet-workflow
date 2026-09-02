"""Legal Document Review agent graph (task 12.2, dept scenario 10).

Node order: killswitch_gate -> retrieve_playbooks (legal-playbooks KB, local
embeddings — the collection is confidential/allow-local-only) -> review (local
14B clause extraction against the retrieved excerpts) -> END.

**No tools, no HITL, no writes.** The scenario's rollout is "assist permanently
(advisory)": the output is a cited draft for counsel, and there is no external
system to act on, so there is deliberately no tool surface to gate. The
guardrail that matters here is the citation resolution in
agents.legal_review.findings — a finding that cannot be tied to a retrieved
playbook excerpt does not enter `findings`, so counsel never reads an advisory
claim with an unverifiable playbook reference.

If retrieval returns nothing the run is `blocked`: with no playbook to compare
against, every possible finding would be uncitable, and a review with zero
findings would read as "this contract is clean" — the dangerous failure mode for
a legal first pass. Blocking says "I could not review this" instead.

Sensitivity is `confidential` end to end, which routes both the embedding and
the reasoning call to the local lane (see reviewer.py). semantic_cache is off in
the registry: two contracts that look similar are not interchangeable.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from agents.legal_review.findings import FindingsParseError, Review
from agents.legal_review.reviewer import ReasoningClient, review_contract
from core.killswitch import KillSwitch
from langgraph.graph import END, StateGraph


class PlaybookRetrieverLike(Protocol):
    async def retrieve(self, *, query: str) -> list[dict[str, Any]]:
        """Return playbook excerpts as [{"content": str, "chunk_ref": str}, ...]."""
        ...


class LegalReviewState(TypedDict, total=False):
    contract_text: str
    excerpts: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    uncited: list[dict[str, Any]]
    blocked_reason: str | None
    paused: bool


def build_legal_review_graph(
    *,
    llm_client: ReasoningClient,
    playbooks: PlaybookRetrieverLike,
    checkpointer: Any,
    killswitch: KillSwitch | None = None,
    agent_name: str = "legal_review",
) -> Any:
    async def killswitch_gate(state: LegalReviewState) -> dict[str, Any]:
        if killswitch is not None and await killswitch.is_agent_paused(agent_name):
            return {"paused": True}
        return {}

    def route_after_killswitch(state: LegalReviewState) -> str:
        return END if state.get("paused") else "retrieve_playbooks"

    async def retrieve_playbooks(state: LegalReviewState) -> dict[str, Any]:
        excerpts = await playbooks.retrieve(query=state["contract_text"])
        return {"excerpts": excerpts}

    def route_after_retrieve(state: LegalReviewState) -> str:
        if not state.get("excerpts"):
            return "end"
        return "review"

    async def review(state: LegalReviewState) -> dict[str, Any]:
        excerpts = state["excerpts"]
        try:
            result: Review = await review_contract(
                contract_text=state["contract_text"],
                playbook_excerpts=[e["content"] for e in excerpts],
                playbook_refs=[e["chunk_ref"] for e in excerpts],
                llm_client=llm_client,
            )
        except FindingsParseError as exc:
            return {"blocked_reason": f"clause review failed: {exc}"}
        return {
            "findings": [f.as_dict() for f in result.findings],
            "uncited": result.uncited,
        }

    async def end_node(state: LegalReviewState) -> dict[str, Any]:
        if not state.get("excerpts") and not state.get("blocked_reason"):
            return {
                "blocked_reason": (
                    "no legal-playbooks excerpts retrieved — refusing to report a "
                    "clean review with nothing to compare against"
                ),
                "findings": [],
                "uncited": [],
            }
        return {}

    graph = StateGraph(LegalReviewState)
    graph.add_node("killswitch_gate", killswitch_gate)
    graph.add_node("retrieve_playbooks", retrieve_playbooks)
    graph.add_node("review", review)
    graph.add_node("end", end_node)

    graph.set_entry_point("killswitch_gate")
    graph.add_conditional_edges(
        "killswitch_gate",
        route_after_killswitch,
        {END: END, "retrieve_playbooks": "retrieve_playbooks"},
    )
    graph.add_conditional_edges(
        "retrieve_playbooks", route_after_retrieve, {"review": "review", "end": "end"}
    )
    graph.add_edge("review", "end")
    graph.add_edge("end", END)

    return graph.compile(checkpointer=checkpointer)

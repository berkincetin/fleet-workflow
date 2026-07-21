"""LangGraph base graph shared by every agent (task 4.1).

Node order: context builder -> guardrails (in) -> call model (routes
reasoning/utility per AgentSpec.call_tier) -> [HITL interrupt iff the model
requested a tool whose risk_class requires approval, per core.hitl] ->
execute tool -> citation attach.

Per-agent graphs (apps/runtime/agents/<name>/graph.py) build an AgentSpec
(system prompt, tier, tools) and call build_graph(); they do not hand-roll
LangGraph wiring themselves, so every agent gets the guardrail/HITL/citation
nodes for free and consistently (CLAUDE.md rule 6: cross-cutting concerns are
never special-cased around).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, TypedDict

from core.citations import Citation, attach_citations
from core.guardrails import detect_injection
from core.hitl import requires_approval
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt


class ReasoningUtilityClient(Protocol):
    async def reasoning(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...
    async def utility(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


ToolFn = Callable[..., Awaitable[Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    risk_class: str  # read | write:internal | write:external
    fn: ToolFn


@dataclass(frozen=True)
class AgentSpec:
    name: str
    system_prompt: str
    call_tier: str = "reasoning"  # reasoning | utility (§4.3)
    tools: list[ToolSpec] = field(default_factory=list)
    eval_pass_rate: float = 0.0
    autonomy_enabled: bool = False
    citations: list[Citation] = field(default_factory=list)


class GraphState(TypedDict, total=False):
    messages: list[dict[str, Any]]
    injection_flagged: bool
    tool_call: dict[str, Any] | None
    tool_result: Any
    rejected: bool
    citations: list[dict[str, Any]]
    text: str


def _tool_by_name(spec: AgentSpec, name: str) -> ToolSpec | None:
    return next((t for t in spec.tools if t.name == name), None)


def build_graph(
    spec: AgentSpec,
    *,
    llm_client: ReasoningUtilityClient,
    checkpointer: Any,
) -> Any:
    """Compile the base graph for one agent, bound to a checkpointer for resume."""

    async def context_builder(state: GraphState) -> dict[str, Any]:
        # Per-agent memory/KB augmentation (core.memory rolling summary, RAG
        # retrieval) happens here in a real agent's own node before this base
        # graph's call_model; the base graph itself only guarantees the slot.
        return {}

    async def guardrails_in(state: GraphState) -> dict[str, Any]:
        last_user = next(
            (m["content"] for m in reversed(state["messages"]) if m.get("role") == "user"), ""
        )
        return {"injection_flagged": detect_injection(last_user)}

    async def call_model(state: GraphState) -> dict[str, Any]:
        caller = llm_client.utility if spec.call_tier == "utility" else llm_client.reasoning
        response = await caller(
            [{"role": "system", "content": spec.system_prompt}, *state["messages"]]
        )
        tool_call = getattr(response, "tool_call", None)
        return {"text": response.content, "tool_call": tool_call}

    def route_after_model(state: GraphState) -> str:
        tool_call = state.get("tool_call")
        if not tool_call:
            return "citation_attach"
        tool = _tool_by_name(spec, tool_call["name"])
        if tool is None:
            return "citation_attach"
        if requires_approval(
            risk_class=tool.risk_class,
            eval_pass_rate=spec.eval_pass_rate,
            autonomy_enabled=spec.autonomy_enabled,
        ):
            return "hitl"
        return "execute_tool"

    async def hitl(state: GraphState) -> dict[str, Any]:
        tool_call = state["tool_call"]
        assert tool_call is not None
        tool = _tool_by_name(spec, tool_call["name"])
        assert tool is not None
        decision = interrupt(
            {
                "tool": tool_call["name"],
                "args": tool_call.get("args", {}),
                "risk_class": tool.risk_class,
            }
        )
        if not decision.get("approved"):
            return {"rejected": True, "tool_call": None}
        return {}

    def route_after_hitl(state: GraphState) -> str:
        if state.get("rejected"):
            return "citation_attach"
        return "execute_tool"

    async def execute_tool(state: GraphState) -> dict[str, Any]:
        tool_call = state["tool_call"]
        assert tool_call is not None
        tool = _tool_by_name(spec, tool_call["name"])
        assert tool is not None
        result = await tool.fn(**tool_call.get("args", {}))
        return {"tool_result": result}

    async def citation_attach(state: GraphState) -> dict[str, Any]:
        attached = attach_citations({"text": state.get("text", "")}, spec.citations)
        return {"citations": attached["citations"]}

    graph = StateGraph(GraphState)
    graph.add_node("context_builder", context_builder)
    graph.add_node("guardrails_in", guardrails_in)
    graph.add_node("call_model", call_model)
    graph.add_node("hitl", hitl)
    graph.add_node("execute_tool", execute_tool)
    graph.add_node("citation_attach", citation_attach)

    graph.set_entry_point("context_builder")
    graph.add_edge("context_builder", "guardrails_in")
    graph.add_edge("guardrails_in", "call_model")
    graph.add_conditional_edges(
        "call_model",
        route_after_model,
        {"hitl": "hitl", "execute_tool": "execute_tool", "citation_attach": "citation_attach"},
    )
    graph.add_conditional_edges(
        "hitl",
        route_after_hitl,
        {"execute_tool": "execute_tool", "citation_attach": "citation_attach"},
    )
    graph.add_edge("execute_tool", "citation_attach")
    graph.add_edge("citation_attach", END)

    return graph.compile(checkpointer=checkpointer)

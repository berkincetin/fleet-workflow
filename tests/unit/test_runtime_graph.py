"""Runtime base graph (task 4.1). AC: unit with FakeLLM — routing utility-vs-
reasoning, interrupt fires on write:external tool, resume completes.

Uses LangGraph's InMemorySaver as the checkpointer (same interrupt/resume
semantics as AsyncPostgresSaver, no real Postgres needed for this unit test);
the live Postgres checkpointer wiring is exercised in
tests/integration/test_runtime_graph_live.py.
"""

from __future__ import annotations

from typing import Any

from core.graph import AgentSpec, ToolSpec, build_graph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class _FakeLLMClient:
    """Records which tier (reasoning/utility) was called and returns a canned reply."""

    def __init__(self, *, tool_call: dict[str, Any] | None = None, reply: str = "done") -> None:
        self._tool_call = tool_call
        self._reply = reply
        self.reasoning_calls: list[list[dict]] = []
        self.utility_calls: list[list[dict]] = []

    async def reasoning(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        self.reasoning_calls.append(messages)
        return _Resp(self._reply, self._tool_call)

    async def utility(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        self.utility_calls.append(messages)
        return _Resp(self._reply, self._tool_call)


class _Resp:
    def __init__(self, content: str, tool_call: dict[str, Any] | None) -> None:
        self.content = content
        self.tool_call = tool_call


async def _noop_tool(**kwargs: Any) -> str:
    return "tool result"


def _spec(*, tier: str = "reasoning", tool_call: dict[str, Any] | None = None) -> AgentSpec:
    return AgentSpec(
        name="test_agent",
        system_prompt="You are a test agent.",
        call_tier=tier,
        tools=[ToolSpec(name="send_email", risk_class="write:external", fn=_noop_tool)],
    )


async def test_graph_routes_to_utility_tier() -> None:
    llm = _FakeLLMClient()
    graph = build_graph(_spec(tier="utility"), llm_client=llm, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "t1"}}
    await graph.ainvoke({"messages": [{"role": "user", "content": "classify this"}]}, config)
    assert llm.utility_calls
    assert llm.reasoning_calls == []


async def test_graph_routes_to_reasoning_tier() -> None:
    llm = _FakeLLMClient()
    graph = build_graph(_spec(tier="reasoning"), llm_client=llm, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "t2"}}
    await graph.ainvoke({"messages": [{"role": "user", "content": "plan this"}]}, config)
    assert llm.reasoning_calls
    assert llm.utility_calls == []


async def test_graph_interrupts_on_write_external_tool_call() -> None:
    llm = _FakeLLMClient(
        tool_call={"name": "send_email", "args": {"to": "customer@example.com"}}
    )
    graph = build_graph(_spec(), llm_client=llm, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "t3"}}
    result = await graph.ainvoke({"messages": [{"role": "user", "content": "email them"}]}, config)

    assert "__interrupt__" in result
    interrupt_payload = result["__interrupt__"][0].value
    assert interrupt_payload["tool"] == "send_email"
    assert interrupt_payload["risk_class"] == "write:external"


async def test_graph_resume_after_approval_completes_the_tool_call() -> None:
    llm = _FakeLLMClient(
        tool_call={"name": "send_email", "args": {"to": "customer@example.com"}}
    )
    checkpointer = InMemorySaver()
    graph = build_graph(_spec(), llm_client=llm, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "t4"}}

    interrupted = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "email them"}]}, config
    )
    assert "__interrupt__" in interrupted

    resumed = await graph.ainvoke(Command(resume={"approved": True}), config)

    assert "__interrupt__" not in resumed
    assert resumed["tool_result"] == "tool result"


async def test_graph_resume_after_rejection_skips_the_tool_call() -> None:
    llm = _FakeLLMClient(
        tool_call={"name": "send_email", "args": {"to": "customer@example.com"}}
    )
    checkpointer = InMemorySaver()
    graph = build_graph(_spec(), llm_client=llm, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "t5"}}

    await graph.ainvoke({"messages": [{"role": "user", "content": "email them"}]}, config)
    resumed = await graph.ainvoke(Command(resume={"approved": False}), config)

    assert "__interrupt__" not in resumed
    assert resumed.get("tool_result") is None
    assert resumed["rejected"] is True

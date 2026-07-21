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
from core.killswitch import KillSwitch
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


class _FakeRedis:
    def __init__(self, store: dict[str, str] | None = None) -> None:
        self.store = store or {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value


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


async def test_graph_short_circuits_when_agent_is_paused() -> None:
    llm = _FakeLLMClient()
    redis = _FakeRedis({"agent:paused:test_agent": "1"})
    graph = build_graph(
        _spec(), llm_client=llm, checkpointer=InMemorySaver(), killswitch=KillSwitch(redis)
    )
    config = {"configurable": {"thread_id": "t6"}}
    result = await graph.ainvoke({"messages": [{"role": "user", "content": "hi"}]}, config)

    assert result["paused"] is True
    assert llm.reasoning_calls == []
    assert llm.utility_calls == []


async def test_graph_runs_normally_when_agent_not_paused() -> None:
    llm = _FakeLLMClient()
    redis = _FakeRedis()
    graph = build_graph(
        _spec(), llm_client=llm, checkpointer=InMemorySaver(), killswitch=KillSwitch(redis)
    )
    config = {"configurable": {"thread_id": "t7"}}
    result = await graph.ainvoke({"messages": [{"role": "user", "content": "hi"}]}, config)

    assert not result.get("paused")
    assert llm.reasoning_calls


async def test_graph_blocks_write_tool_when_global_read_only() -> None:
    """A write:internal tool with autonomy already granted reaches execute_tool
    directly (no HITL stop) — the read-only gate must still catch it there."""
    llm = _FakeLLMClient(
        tool_call={"name": "log_note", "args": {"note": "customer called"}}
    )
    redis = _FakeRedis({"global:read_only": "1"})
    autonomous_spec = AgentSpec(
        name="test_agent",
        system_prompt="You are a test agent.",
        tools=[ToolSpec(name="log_note", risk_class="write:internal", fn=_noop_tool)],
        eval_pass_rate=0.95,
        autonomy_enabled=True,
    )
    graph = build_graph(
        autonomous_spec, llm_client=llm, checkpointer=InMemorySaver(),
        killswitch=KillSwitch(redis),
    )
    config = {"configurable": {"thread_id": "t8"}}
    result = await graph.ainvoke({"messages": [{"role": "user", "content": "log this"}]}, config)

    assert "__interrupt__" not in result
    assert result.get("tool_result") is None
    assert result["blocked_read_only"] is True


async def test_graph_blocks_approved_tool_if_read_only_flips_after_interrupt() -> None:
    """Read-only can be flipped on by an admin while a HITL approval is
    pending; the gate at execute_tool must still catch it after resume."""
    llm = _FakeLLMClient(
        tool_call={"name": "send_email", "args": {"to": "customer@example.com"}}
    )
    redis = _FakeRedis()
    ks = KillSwitch(redis)
    checkpointer = InMemorySaver()
    graph = build_graph(_spec(), llm_client=llm, checkpointer=checkpointer, killswitch=ks)
    config = {"configurable": {"thread_id": "t9"}}

    await graph.ainvoke({"messages": [{"role": "user", "content": "email them"}]}, config)
    await ks.set_global_read_only(True)
    resumed = await graph.ainvoke(Command(resume={"approved": True}), config)

    assert "__interrupt__" not in resumed
    assert resumed.get("tool_result") is None
    assert resumed["blocked_read_only"] is True

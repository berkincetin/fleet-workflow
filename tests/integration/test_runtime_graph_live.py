"""Integration: the runtime base graph against a REAL Postgres checkpointer
(task 4.1 AC — "resume completes" proven against real infra, not InMemorySaver)
and the real LLM gateway (task 2.3's LLMClient), so both the checkpoint
persistence and the reasoning/utility routing are exercised live.

Uses a FakeLLM-shaped stub only for the tool-call branch (the gateway proxy
has no notion of "call this tool"), matching how a real agent's call_model
node would parse a tool-call out of the model's structured output — the base
graph itself is agent-agnostic and unit-tested with FakeLLM in
tests/unit/test_runtime_graph.py; this test's job is only to prove the
checkpointer round-trips through real Postgres.
"""

from __future__ import annotations

import asyncio
import sys
import uuid

import httpx
import pytest
from core.graph import AgentSpec, ToolSpec, build_graph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

if sys.platform == "win32":
    # psycopg's async mode cannot run on Windows' default ProactorEventLoop
    # (raises psycopg.InterfaceError on connect); production runs under
    # uvicorn on Linux and is unaffected — this is test-infra-only, same class
    # of Windows-specific fixup as the asyncpg event-loop notes elsewhere in
    # tests/integration/.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

KEYCLOAK_BASE = "http://localhost:8080"
CHECKPOINT_DB_URL = "postgresql://fleet:fleet_dev_pw@localhost:5432/fleet"


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _stack_up(), reason="dev stack not reachable — start with `make dev`"
)


class _ToolCallingLLM:
    """Always proposes the same write:external tool call, regardless of tier."""

    async def reasoning(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        return _Resp()

    async def utility(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        return _Resp()


class _Resp:
    content = "I'll send that email."
    tool_call = {"name": "send_email", "args": {"to": "customer@example.com"}}


async def _send_email(**kwargs: object) -> str:
    return "sent"


async def test_graph_interrupt_and_resume_survive_a_real_postgres_checkpoint() -> None:
    thread_id = f"live-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    spec = AgentSpec(
        name="live_test_agent",
        system_prompt="test",
        tools=[ToolSpec(name="send_email", risk_class="write:external", fn=_send_email)],
    )

    async with AsyncPostgresSaver.from_conn_string(CHECKPOINT_DB_URL) as checkpointer:
        await checkpointer.setup()

        graph = build_graph(spec, llm_client=_ToolCallingLLM(), checkpointer=checkpointer)
        interrupted = await graph.ainvoke(
            {"messages": [{"role": "user", "content": "email the customer"}]}, config
        )
        assert "__interrupt__" in interrupted

        # Rebuild the graph fresh (new process would do this too) bound to the
        # SAME checkpointer/thread_id, proving resume works off persisted state,
        # not in-process memory.
        graph2 = build_graph(spec, llm_client=_ToolCallingLLM(), checkpointer=checkpointer)
        resumed = await graph2.ainvoke(Command(resume={"approved": True}), config)

    assert "__interrupt__" not in resumed
    assert resumed["tool_result"] == "sent"

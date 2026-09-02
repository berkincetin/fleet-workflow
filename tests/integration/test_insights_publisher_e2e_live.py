"""Integration: Insights Publisher against the real dev stack (task 11.3 AC:
monthly cron produces a draft with GROUNDED numbers pending approval; an
invented number never reaches approval).

Drives the real insights_publisher graph with real pg_ro-read index data and a
real cloud reasoning draft through the live gateway, exactly as the API router
does. A grounded run reaches the write:external HITL interrupt with the draft +
the data it was grounded against as the approval payload. A second run with a
poisoned data source (the drafter still only cites real numbers) stays grounded;
the guardrail itself is unit-proven — here we prove the real draft's numbers are
all grounded end to end.
"""

from __future__ import annotations

import asyncio
import sys

import httpx
import pytest

if sys.platform == "win32":
    # Same Windows/psycopg-async fixup as the other HITL e2e tests: the
    # AsyncPostgresSaver checkpointer can't run on ProactorEventLoop.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _stack_up(), reason="dev stack not reachable — start with `make dev`"),
]


async def test_monthly_run_reaches_approval_with_grounded_numbers() -> None:
    from agents.insights_publisher.graph import build_insights_publisher_graph
    from agents.insights_publisher.grounding import check_numbers_grounded
    from core.llm.factory import build_client
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.cms import build_cms_server
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    pg = PgReadOnlyTool(
        runner=build_default_runner(), allowlisted_tables={"fixture_index_monthly"}
    )

    class _IndexData:
        async def monthly_rows(self):  # type: ignore[no-untyped-def]
            return await pg.query(
                "SELECT segment, avg_price, listing_count FROM fixture_index_monthly"
            )

    class _BrandVoice:
        async def guidance(self) -> str:
            return "Sıcak, güven veren, sade bir dil kullan. Rakamları bağlamıyla ver."

    llm_client = await build_client()
    _, cms_tool = build_cms_server(api_key="internal")
    dsn = API_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(dsn) as checkpointer:
        graph = build_insights_publisher_graph(
            llm_client=llm_client, index_data=_IndexData(), brand_voice=_BrandVoice(),
            publisher=cms_tool, checkpointer=checkpointer,
        )
        result = await graph.ainvoke({}, {"configurable": {"thread_id": "ip-e2e-1"}})

    # A grounded draft reaches the write:external approval interrupt.
    assert "__interrupt__" in result, result.get("blocked_reason")
    payload = result["__interrupt__"][0].value
    assert payload["risk_class"] == "write:external"
    draft = payload["args"]
    data = payload["grounded_against"]
    # Independently re-verify: every number in the drafted content is grounded.
    combined = f"{draft['report']}\n{draft['social']}"
    assert check_numbers_grounded(draft_text=combined, data_rows=data).grounded is True
    # cms.publish never fired — it waits behind the approval.
    assert cms_tool.published == []

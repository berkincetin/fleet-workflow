"""Insights Publisher run trigger (task 11.3, dept scenario 08).

`POST /v1/insights-publisher/runs` starts a monthly-report run: pull the index
data, draft a report + social in brand voice, run the numbers-match grounding
guardrail, and (if grounded) interrupt for approval. cms.publish + social.post
are write:external, so every grounded run ends at the approval interrupt with
the draft and the data it was grounded against as the approval payload — same
"persist a pending Approval row, return pending_approval" shape as
routers/invoice_agent.py. An ungrounded draft returns `blocked` with the
offending numbers and creates no Approval row (a human is never asked to approve
an invented statistic).

Reachable by a Keycloak human with MANAGE_AGENTS or a Fleet API key with the
`insights_publish` scope — the n8n monthly cron path.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.db import get_session
from fleet_api.models import Agent, Approval
from fleet_api.rbac import Permission
from fleet_api.service_auth import require_user_or_service_scope
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/insights-publisher", tags=["insights-publisher"])

INSIGHTS_PUBLISHER_AGENT_NAME = "insights_publisher"


class RunOut(BaseModel):
    run_id: str
    status: str  # "pending_approval" | "blocked"
    detail: dict[str, Any]


@router.post("/runs", status_code=201)
async def start_run(
    _: object = Depends(  # noqa: B008
        require_user_or_service_scope(Permission.MANAGE_AGENTS, "insights_publish")
    ),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunOut:
    from agents.insights_publisher.graph import build_insights_publisher_graph
    from core.llm.factory import build_client
    from fleet_api.db import database_url as api_database_url
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.cms import build_cms_server
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    agent_row = (
        await session.execute(
            select(Agent).where(Agent.name == INSIGHTS_PUBLISHER_AGENT_NAME)
        )
    ).scalar_one_or_none()
    if agent_row is None:
        raise HTTPException(
            status_code=500, detail="insights_publisher not seeded — run `make seed`"
        )

    llm_client = await build_client()
    pg = PgReadOnlyTool(
        runner=build_default_runner(), allowlisted_tables={"fixture_index_monthly"}
    )
    _, cms_tool = build_cms_server(api_key="internal")

    class _IndexData:
        async def monthly_rows(self) -> list[dict[str, Any]]:
            rows: list[dict[str, Any]] = await pg.query(
                "SELECT segment, avg_price, listing_count FROM fixture_index_monthly"
            )
            return rows

    class _BrandVoice:
        async def guidance(self) -> str:
            # INTEGRATION-POINT: brand-voice text would come from the mkt-brand
            # collection; a fixed exemplar stands in for the demo.
            return (
                "Sıcak, güven veren, sade bir dil kullan. Abartıdan kaçın; "
                "rakamları bağlamıyla ver. Okuyucuya doğrudan hitap et."
            )

    run_id = str(uuid.uuid4())
    checkpoint_dsn = api_database_url().replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn) as checkpointer:
        graph = build_insights_publisher_graph(
            llm_client=llm_client, index_data=_IndexData(), brand_voice=_BrandVoice(),
            publisher=cms_tool, checkpointer=checkpointer,
        )
        result = await graph.ainvoke({}, {"configurable": {"thread_id": run_id}})

    if result.get("blocked_reason"):
        return RunOut(
            run_id=run_id, status="blocked",
            detail={
                "reason": result["blocked_reason"],
                "unmatched_numbers": result.get("unmatched_numbers", []),
            },
        )

    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        approval = Approval(
            agent_id=agent_row.id,
            run_id=run_id,
            action=payload["tool"],
            payload=payload["args"],
            status="pending",
        )
        session.add(approval)
        await session.commit()
        return RunOut(
            run_id=run_id, status="pending_approval",
            detail={"approval_payload": payload},
        )

    return RunOut(run_id=run_id, status="blocked", detail={"reason": "no draft produced"})

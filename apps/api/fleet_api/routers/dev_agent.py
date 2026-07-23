"""Dev Agent run trigger (task 5.5, dept scenario 03).

`POST /v1/dev-agent/runs` starts a labeled-ticket run: builds the real Dev
Agent graph (Jira/GitHub/Slack MCP tools, real gateway client, real
AsyncPostgresSaver checkpointer) and invokes it. github.open_pr is always
write:external, so every successful run reaches the HITL interrupt — this
endpoint persists that as a pending `Approval` row (run_id == the graph's
thread_id) for the approvals queue (routers/approvals.py) to list and later
resume. A run that never reaches the interrupt (guardrail block: unlabeled
ticket, protected path, oversized diff) returns its blocked_reason directly,
no Approval row created.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.db import get_session
from fleet_api.models import Agent, Approval
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/dev-agent", tags=["dev-agent"])

DEV_AGENT_NAME = "dev_agent"
SLACK_CHANNEL = "#dev-agent"


class RunIn(BaseModel):
    ticket_key: str


class RunOut(BaseModel):
    run_id: str
    status: str  # "pending_approval" | "blocked"
    detail: dict[str, Any]


class TicketOut(BaseModel):
    key: str
    summary: str
    labels: list[str]


@router.get("/tickets")
async def list_tickets(
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
) -> list[TicketOut]:
    """Fixture tickets for a run-dialog picker (task 6.5.3, examples gallery
    try-it flow) — sourced from the same DEMO_FIXTURE_TICKETS the fixture Jira
    backend and dev_agent evals use, so the picker never drifts from what a
    run actually resolves against."""
    from fleet_mcp.servers.jira import DEMO_FIXTURE_TICKETS

    return [
        TicketOut(key=t["key"], summary=t["summary"], labels=t["labels"])
        for t in DEMO_FIXTURE_TICKETS.values()
    ]


@router.post("/runs", status_code=201)
async def start_run(
    body: RunIn,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunOut:
    from agents.dev_agent.graph import build_dev_agent_graph
    from core.llm.factory import build_client
    from fleet_api.db import database_url as api_database_url
    from fleet_mcp.servers.github import GitHubTool
    from fleet_mcp.servers.github import build_default_backend as build_github_backend
    from fleet_mcp.servers.jira import JiraTool
    from fleet_mcp.servers.jira import build_default_backend as build_jira_backend
    from fleet_mcp.servers.slack import SlackPostTool, build_default_sender
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    agent_row = (
        await session.execute(select(Agent).where(Agent.name == DEV_AGENT_NAME))
    ).scalar_one_or_none()
    if agent_row is None:
        raise HTTPException(status_code=500, detail="dev_agent not seeded — run `make seed`")

    llm_client = await build_client()
    jira = JiraTool(backend=build_jira_backend())
    github = GitHubTool(backend=build_github_backend())
    slack = SlackPostTool(sender=build_default_sender(), allowed_channels={SLACK_CHANNEL})

    run_id = str(uuid.uuid4())
    checkpoint_dsn = api_database_url().replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn) as checkpointer:
        graph = build_dev_agent_graph(
            llm_client=llm_client, jira=jira, github=github, slack=slack,
            checkpointer=checkpointer, slack_channel=SLACK_CHANNEL,
        )
        config = {"configurable": {"thread_id": run_id}}
        result = await graph.ainvoke({"ticket_key": body.ticket_key}, config)

    if result.get("blocked_reason"):
        return RunOut(run_id=run_id, status="blocked", detail={"reason": result["blocked_reason"]})

    if "__interrupt__" in result:
        interrupt_payload = result["__interrupt__"][0].value
        approval = Approval(
            agent_id=agent_row.id,
            run_id=run_id,
            action=interrupt_payload["tool"],
            payload=interrupt_payload["args"],
            status="pending",
        )
        session.add(approval)
        await session.commit()
        return RunOut(
            run_id=run_id, status="pending_approval", detail={"approval_payload": interrupt_payload}
        )

    # Should not happen for a well-formed graph (every non-blocked path ends
    # at the interrupt before this endpoint returns) — surfaced rather than
    # silently swallowed if it ever does.
    raise HTTPException(status_code=500, detail=f"unexpected run result: {result!r}")

"""Approval queue: list pending items, approve/edit/reject with LangGraph
resume (task 5.4, TRD §9).

`GET /v1/approvals` lists pending rows (APPROVE-gated: approver/dept_admin/
platform_admin per §7.1). `POST /v1/approvals/{id}/decide` writes the
decision (status/decided_by/decided_at) and resumes the paused graph run via
`Command(resume=...)` bound to the approval's `run_id` (== the graph's
`thread_id`) against a real AsyncPostgresSaver — same mechanism proven in
task 4.1's test_runtime_graph_live.py, now reachable from the API.

Dev Agent (5.5) was the only interrupt-producing agent through Sprint 5, so
the resume path stayed dev-agent-specific rather than a generic per-agent
registry (CLAUDE.md: no premature abstraction) — Invoice Agent (6.3) is that
second interrupt-producing agent, the trigger already flagged for extracting
one. `_RESUMERS` is a small dict keyed by `agents.name`, not a class
hierarchy/plugin system — still the simplest thing that lets a third agent
register itself with one new entry and one new function, not a framework.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.db import get_session
from fleet_api.models import Agent, Approval
from fleet_api.rbac import Permission, require_permission
from langgraph.types import Command
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


class ApprovalOut(BaseModel):
    id: int
    agent_id: int
    run_id: str
    action: str
    payload: dict[str, Any]
    status: str
    decided_by: str | None
    decided_at: dt.datetime | None
    sla_at: dt.datetime | None

    model_config = {"from_attributes": True}


class DecisionIn(BaseModel):
    decision: str  # "approve" | "reject"
    edited_payload: dict[str, Any] | None = None


@router.get("")
async def list_approvals(
    status: str = "pending",
    _: object = Depends(require_permission(Permission.APPROVE)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[ApprovalOut]:
    rows = (
        await session.execute(
            select(Approval).where(Approval.status == status).order_by(Approval.created_at)
        )
    ).scalars().all()
    return [ApprovalOut.model_validate(r) for r in rows]


async def _resume_dev_agent_run(run_id: str, *, approved: bool) -> None:
    """Rebuild the Dev Agent graph bound to the approval's run_id (thread_id)
    against the real Postgres checkpointer and resume it — mirrors
    test_runtime_graph_live.py's "rebuild fresh, resume off persisted state"
    proof, now the real resume path a live approval decision drives."""
    from agents.dev_agent.graph import build_dev_agent_graph
    from core.llm.factory import build_client
    from fleet_api.db import database_url as api_database_url
    from fleet_mcp.servers.github import GitHubTool
    from fleet_mcp.servers.github import build_default_backend as build_github_backend
    from fleet_mcp.servers.jira import JiraTool
    from fleet_mcp.servers.jira import build_default_backend as build_jira_backend
    from fleet_mcp.servers.slack import SlackPostTool, build_default_sender
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    llm_client = await build_client()
    jira = JiraTool(backend=build_jira_backend())
    github = GitHubTool(backend=build_github_backend())
    slack = SlackPostTool(sender=build_default_sender(), allowed_channels={"#dev-agent"})

    checkpoint_dsn = api_database_url().replace("postgresql+asyncpg://", "postgresql://")
    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn) as checkpointer:
        graph = build_dev_agent_graph(
            llm_client=llm_client, jira=jira, github=github, slack=slack,
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": run_id}}
        await graph.ainvoke(Command(resume={"approved": approved}), config)


async def _resume_invoice_agent_run(run_id: str, *, approved: bool) -> None:
    """Same rebuild-fresh-and-resume mechanism as Dev Agent, for Invoice
    Agent's erp.create_draft_entry interrupt (task 6.3)."""
    from agents.invoice_agent.graph import build_invoice_agent_graph
    from agents.invoice_agent.po_lookup import PgPoLookup
    from core.llm.factory import build_client
    from fleet_api.db import database_url as api_database_url
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.erp import ErpTool
    from fleet_mcp.servers.ocr import build_ocr_tool
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    llm_client = await build_client()
    ocr = build_ocr_tool(vision_client=llm_client, tesseract_fn=lambda b: "")
    erp = ErpTool()
    po_lookup = PgPoLookup(
        tool=PgReadOnlyTool(
            runner=build_default_runner(), allowlisted_tables={"fixture_purchase_orders"}
        )
    )

    checkpoint_dsn = api_database_url().replace("postgresql+asyncpg://", "postgresql://")
    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn) as checkpointer:
        graph = build_invoice_agent_graph(
            llm_client=llm_client, ocr=_OcrToolAdapter(ocr), erp=erp, po_lookup=po_lookup,
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": run_id}}
        await graph.ainvoke(Command(resume={"approved": approved}), config)


class _OcrToolAdapter:
    """`build_ocr_tool` returns a bare callable (`image_base64 -> {text, source}`);
    `InvoiceAgentState`'s OcrLike Protocol expects an `.extract_text(...)`
    method — this adapts one to the other rather than changing either
    established shape for the sake of the other."""

    def __init__(self, fn: Any) -> None:
        self._fn = fn

    async def extract_text(self, image_base64: str) -> dict[str, Any]:
        return await self._fn(image_base64=image_base64)  # type: ignore[no-any-return]


# Keyed by agents.name (TRD §11) — the same identifier already carried on
# every Approval row's agent_id -> agents.name join. A third interrupt-
# producing agent registers here with one new entry, no other code change.
_RESUMERS: dict[str, Callable[..., Awaitable[None]]] = {
    "dev_agent": _resume_dev_agent_run,
    "invoice_agent": _resume_invoice_agent_run,
}


@router.post("/{approval_id}/decide", status_code=200)
async def decide_approval(
    approval_id: int,
    body: DecisionIn,
    current: CurrentUser = Depends(get_current_user),  # noqa: B008
    _: object = Depends(require_permission(Permission.APPROVE)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ApprovalOut:
    if body.decision not in ("approve", "reject"):
        raise HTTPException(status_code=422, detail="decision must be 'approve' or 'reject'")

    approval = await session.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"approval already {approval.status}")

    if body.edited_payload is not None:
        approval.payload = body.edited_payload

    agent_row = await session.get(Agent, approval.agent_id)
    agent_label = agent_row.name if agent_row is not None else f"id={approval.agent_id}"
    if agent_row is None or agent_row.name not in _RESUMERS:
        raise HTTPException(
            status_code=500,
            detail=f"no resume handler registered for agent {agent_label!r}",
        )
    resume_fn = _RESUMERS[agent_row.name]

    approval.status = "approved" if body.decision == "approve" else "rejected"
    approval.decided_by = current.sub
    approval.decided_at = dt.datetime.now(dt.UTC)
    await session.commit()
    await session.refresh(approval)

    await resume_fn(approval.run_id, approved=body.decision == "approve")

    return ApprovalOut.model_validate(approval)

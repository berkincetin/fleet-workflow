"""Invoice Agent run trigger (task 6.3, dept scenario 04 Invoice & Reconciliation).

`POST /v1/invoice-agent/runs` starts a run from an already-uploaded invoice
image (base64): OCR extract -> field extraction -> validation against the
fixture PO table -> HITL interrupt. erp.create_draft_entry is always
write:external, so every run that reaches extraction successfully ends at
the interrupt — same "persist a pending Approval row, return pending_approval
status" shape as `routers/dev_agent.py`. A run that fails extraction (garbled
OCR text, model returned malformed JSON) returns its blocked_reason directly,
no Approval row created — same shape as a Dev Agent guardrail block.

Reachable by EITHER a Keycloak-authenticated human with MANAGE_AGENTS (e.g. a
future admin UI triggering a run directly) OR a Fleet API key with the
`invoice_intake` scope — the department scenario's "webhook/manual upload"
intake path (task 6.3) is n8n calling this endpoint with no Keycloak session
at all, the same "programmatic access" leg task 6.1 built for `/v1/service/*`.
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

router = APIRouter(prefix="/v1/invoice-agent", tags=["invoice-agent"])

INVOICE_AGENT_NAME = "invoice_agent"


class RunIn(BaseModel):
    image_base64: str


class RunOut(BaseModel):
    run_id: str
    status: str  # "pending_approval" | "blocked"
    detail: dict[str, Any]


@router.post("/runs", status_code=201)
async def start_run(
    body: RunIn,
    _: object = Depends(  # noqa: B008
        require_user_or_service_scope(Permission.MANAGE_AGENTS, "invoice_intake")
    ),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunOut:
    from agents.invoice_agent.graph import build_invoice_agent_graph
    from agents.invoice_agent.po_lookup import PgPoLookup
    from core.llm.factory import build_client
    from fleet_api.db import database_url as api_database_url
    from fleet_api.routers.approvals import _OcrToolAdapter
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.erp import ErpTool
    from fleet_mcp.servers.ocr import build_ocr_tool
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool
    from fleet_rag.ingest.ocr import tesseract_ocr
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    agent_row = (
        await session.execute(select(Agent).where(Agent.name == INVOICE_AGENT_NAME))
    ).scalar_one_or_none()
    if agent_row is None:
        raise HTTPException(status_code=500, detail="invoice_agent not seeded — run `make seed`")

    llm_client = await build_client()
    ocr = _OcrToolAdapter(
        build_ocr_tool(
            vision_client=llm_client, tesseract_fn=tesseract_ocr, sensitivity="confidential"
        )
    )
    erp = ErpTool()
    po_lookup = PgPoLookup(
        tool=PgReadOnlyTool(
            runner=build_default_runner(), allowlisted_tables={"fixture_purchase_orders"}
        )
    )

    run_id = str(uuid.uuid4())
    checkpoint_dsn = api_database_url().replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn) as checkpointer:
        graph = build_invoice_agent_graph(
            llm_client=llm_client, ocr=ocr, erp=erp, po_lookup=po_lookup,
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": run_id}}
        result = await graph.ainvoke({"image_base64": body.image_base64}, config)

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

    raise HTTPException(status_code=500, detail=f"unexpected run result: {result!r}")

"""HR Agent run trigger (task 8.5, dept scenario 05 HR Talent & Onboarding).

`POST /v1/hr-agent/runs` starts a run from an already-uploaded CV image
(base64) plus the role's required criteria: OCR extract (local, pii lane) ->
structured profile extraction (local Qwen) -> role match scoring -> HITL
interrupt. hr.shortlist_draft is always write:internal with autonomy off, so
every run that reaches extraction successfully ends at the interrupt — same
shape as routers/invoice_agent.py and routers/dev_agent.py.
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

router = APIRouter(prefix="/v1/hr-agent", tags=["hr-agent"])

HR_AGENT_NAME = "hr_agent"


class RunIn(BaseModel):
    image_base64: str
    criteria: list[str] = []


class RunOut(BaseModel):
    run_id: str
    status: str  # "pending_approval" | "blocked"
    detail: dict[str, Any]


@router.post("/runs", status_code=201)
async def start_run(
    body: RunIn,
    _: object = Depends(  # noqa: B008
        require_user_or_service_scope(Permission.MANAGE_AGENTS, "hr_intake")
    ),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunOut:
    from agents.hr_agent.graph import build_hr_agent_graph
    from core.llm.factory import build_client
    from fleet_api.db import database_url as api_database_url
    from fleet_api.routers.approvals import _OcrToolAdapter
    from fleet_mcp.servers.ocr import build_ocr_tool
    from fleet_rag.ingest.ocr import tesseract_ocr
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    agent_row = (
        await session.execute(select(Agent).where(Agent.name == HR_AGENT_NAME))
    ).scalar_one_or_none()
    if agent_row is None:
        raise HTTPException(status_code=500, detail="hr_agent not seeded — run `make seed`")

    llm_client = await build_client()
    ocr = _OcrToolAdapter(
        build_ocr_tool(vision_client=llm_client, tesseract_fn=tesseract_ocr, sensitivity="pii")
    )

    run_id = str(uuid.uuid4())
    checkpoint_dsn = api_database_url().replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn) as checkpointer:
        graph = build_hr_agent_graph(llm_client=llm_client, ocr=ocr, checkpointer=checkpointer)
        config = {"configurable": {"thread_id": run_id}}
        result = await graph.ainvoke(
            {"image_base64": body.image_base64, "criteria": body.criteria}, config
        )

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

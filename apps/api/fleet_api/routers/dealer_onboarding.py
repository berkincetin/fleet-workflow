"""Dealer Onboarding run trigger (task 12.1, dept scenario 09).

`POST /v1/dealer-onboarding/runs` starts a dossier check from an application id
plus the applicant's uploaded documents (base64 images, one per document kind):
CRM fetch -> local OCR -> local pii-lane extraction -> deterministic cross-check
-> one of three outcomes, reflected in the response `status`:

* `pending_approval` — documents are missing, so the TR formal missing-document
  email is waiting on the write:external approval queue. Nothing was sent and
  the application's CRM status is untouched until a human decides
  (`POST /v1/approvals/{id}/decide` resumes the run and sends).
* `flagged` — the certificate names a different company than the application.
  The application moved to `manual_review` and **no email was composed**.
* `completed` — the dossier is clean; the application moved to
  `ready_for_sales` for a corporate-sales rep to pick up.

Reachable by a Keycloak human with MANAGE_AGENTS or a Fleet API key with the
`dealer_onboarding` scope (a CRM-side webhook could drive it that way).
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

router = APIRouter(prefix="/v1/dealer-onboarding", tags=["dealer-onboarding"])

DEALER_ONBOARDING_AGENT_NAME = "dealer_onboarding"


class DocumentIn(BaseModel):
    kind: str  # "authorization_certificate" | "tax_registration"
    image_base64: str


class RunIn(BaseModel):
    application_id: str
    documents: list[DocumentIn] = []


class RunOut(BaseModel):
    run_id: str
    status: str  # "pending_approval" | "flagged" | "completed" | "blocked"
    detail: dict[str, Any]


def build_dealer_onboarding_deps(llm_client: Any) -> tuple[Any, Any, Any]:
    """(ocr, crm_tool, email_tool) wired for a dealer-onboarding run.

    Shared with the approvals resume path so an approved send goes through the
    *same* email tool — domain allowlist included — as the run that queued it.
    """
    from fleet_api.routers.approvals import _OcrToolAdapter
    from fleet_mcp.servers.crm import build_crm_server
    from fleet_mcp.servers.email import EmailSendTool
    from fleet_mcp.servers.ocr import build_ocr_tool
    from fleet_mcp.servers.smtp_sender import build_default_sender
    from fleet_rag.ingest.ocr import tesseract_ocr

    # sensitivity="pii" makes ocr_image skip the cloud vision lane entirely and
    # go straight to local tesseract (TRD §8) — the certificate carries the
    # dealer's tax number and IBAN.
    ocr = _OcrToolAdapter(
        build_ocr_tool(vision_client=llm_client, tesseract_fn=tesseract_ocr, sensitivity="pii")
    )
    _, crm_tool = build_crm_server(api_key="internal")
    email_tool = EmailSendTool(
        sender=build_default_sender(), allowed_domains={"fleet.local", "example.com"}
    )
    return ocr, crm_tool, email_tool


@router.post("/runs", status_code=201)
async def start_run(
    body: RunIn,
    _: object = Depends(  # noqa: B008
        require_user_or_service_scope(Permission.MANAGE_AGENTS, "dealer_onboarding")
    ),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunOut:
    from agents.dealer_onboarding.graph import build_dealer_onboarding_graph
    from core.llm.factory import build_client
    from fleet_api.db import database_url as api_database_url
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    agent_row = (
        await session.execute(
            select(Agent).where(Agent.name == DEALER_ONBOARDING_AGENT_NAME)
        )
    ).scalar_one_or_none()
    if agent_row is None:
        raise HTTPException(
            status_code=500, detail="dealer_onboarding not seeded — run `make seed`"
        )

    llm_client = await build_client()
    ocr, crm_tool, email_tool = build_dealer_onboarding_deps(llm_client)

    run_id = str(uuid.uuid4())
    checkpoint_dsn = api_database_url().replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn) as checkpointer:
        graph = build_dealer_onboarding_graph(
            llm_client=llm_client, ocr=ocr, crm=crm_tool, email=email_tool,
            checkpointer=checkpointer,
        )
        result = await graph.ainvoke(
            {
                "application_id": body.application_id,
                "documents": [d.model_dump() for d in body.documents],
            },
            {"configurable": {"thread_id": run_id}},
        )

    if result.get("blocked_reason"):
        return RunOut(
            run_id=run_id, status="blocked", detail={"reason": result["blocked_reason"]}
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
            detail={"approval_payload": payload, "check": result.get("check", {})},
        )

    check = result.get("check", {})
    status = "flagged" if check.get("name_mismatch") else "completed"
    return RunOut(
        run_id=run_id, status=status,
        detail={"check": check, "status_update": result.get("status_update")},
    )

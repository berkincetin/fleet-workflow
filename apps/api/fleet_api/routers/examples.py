"""Examples gallery (task 6.5.2): per-agent sample tasks for a non-technical
UI, backed by the `eval_cases` table (seeded from evals/datasets/*.jsonl,
source="seed"). A case created here is source="user" — it never touches the
jsonl files directly (the API container has no writable repo checkout); a
builder promotes it into the versioned dataset later via evals/promote.py.

Payload shape is agent-specific (mirrors evals/runner.py's per-agent
dataclasses: EvalCase for support_copilot, AnalyticsCase, DevAgentCase,
InvoiceCase) — validated here against a minimal per-agent required-field set
so a malformed example can't silently corrupt the gallery, without this
router needing to import (or duplicate) the eval runner's full dataclasses.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.db import get_session
from fleet_api.models import EvalCase
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/examples", tags=["examples"])

# Required payload fields per agent, enough to catch a malformed submission
# without re-implementing evals/runner.py's full dataclass validation here.
_REQUIRED_FIELDS: dict[str, set[str]] = {
    "support_copilot": {"id", "question"},
    "analytics": {"id", "question"},
    "dev_agent": {"id", "ticket_key"},
    "invoice_agent": {"id", "vendor", "po_number", "amount"},
    "hr_agent": {"id", "candidate_name"},
}


class ExampleOut(BaseModel):
    id: int
    agent_name: str
    case_id: str
    payload: dict[str, Any]
    source: str
    created_by: str | None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ExampleIn(BaseModel):
    agent_name: str
    payload: dict[str, Any]


def _validate_agent(agent_name: str) -> None:
    if agent_name not in _REQUIRED_FIELDS:
        raise HTTPException(status_code=422, detail=f"unknown agent: {agent_name}")


def _validate_payload(agent_name: str, payload: dict[str, Any]) -> None:
    missing = _REQUIRED_FIELDS[agent_name] - payload.keys()
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"payload missing required fields for {agent_name}: {sorted(missing)}",
        )


@router.get("")
async def list_examples(
    agent: str | None = None,
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[ExampleOut]:
    stmt = select(EvalCase).order_by(EvalCase.agent_name, EvalCase.id)
    if agent is not None:
        stmt = stmt.where(EvalCase.agent_name == agent)
    rows = (await session.execute(stmt)).scalars().all()
    return [ExampleOut.model_validate(r) for r in rows]


@router.post("", status_code=201)
async def create_example(
    body: ExampleIn,
    user: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ExampleOut:
    _validate_agent(body.agent_name)
    _validate_payload(body.agent_name, body.payload)

    case_id = str(body.payload.get("id") or "")
    if not case_id:
        raise HTTPException(status_code=422, detail="payload.id is required")

    existing = (
        await session.execute(
            select(EvalCase).where(
                EvalCase.agent_name == body.agent_name, EvalCase.case_id == case_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="a case with this id already exists")

    row = EvalCase(
        agent_name=body.agent_name,
        case_id=case_id,
        payload=body.payload,
        source="user",
        created_by=getattr(user, "sub", None),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return ExampleOut.model_validate(row)

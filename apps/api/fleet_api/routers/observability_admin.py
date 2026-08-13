"""Cost dashboard + audit explorer (task 7.2, TRD §5/§7.1).

Reads `spend_ledger` (already populated by every real gateway-client call
since task 2.4 — see core.llm.ledger, not the TRD's LiteLLM-webhook design;
a documented Sprint 2 deviation) and `audit_log` (populated by
`AuditMiddleware` on every request since task 1.4). Both are append-only and
platform-wide, so there is no per-dept scoping to enforce here beyond the
MANAGE_PLATFORM gate itself — same tier as models/API-key/user/budget admin.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, Query
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import AuditLog, SpendLedger
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/admin", tags=["admin:observability"])


class SpendByKey(BaseModel):
    key: str
    total_usd: float


class BurnDownPoint(BaseModel):
    date: str
    total_usd: float


class CostSummaryOut(BaseModel):
    total_usd: float
    by_dept: list[SpendByKey]
    by_agent: list[SpendByKey]
    by_model: list[SpendByKey]
    burn_down: list[BurnDownPoint]
    cache_hit_ratio: float


def _round2(v: float | None) -> float:
    return round(float(v or 0.0), 2)


@router.get("/cost/summary")
async def cost_summary(
    days: int = Query(default=30, ge=1, le=365),
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CostSummaryOut:
    since = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
    window = SpendLedger.ts >= since

    total = (
        await session.execute(
            select(func.coalesce(func.sum(SpendLedger.cost_usd), 0)).where(window)
        )
    ).scalar_one()

    async def _group(col: Any) -> list[SpendByKey]:
        rows = (
            await session.execute(
                select(col, func.sum(SpendLedger.cost_usd))
                .where(window)
                .group_by(col)
                .order_by(func.sum(SpendLedger.cost_usd).desc())
            )
        ).all()
        return [
            SpendByKey(key=str(k) if k is not None else "unassigned", total_usd=_round2(v))
            for k, v in rows
        ]

    by_dept = await _group(SpendLedger.dept_id)
    by_agent = await _group(SpendLedger.agent_id)
    by_model = await _group(SpendLedger.model)

    # A single reused expression object, not three separate `func.date_trunc(...)`
    # calls — Postgres rejects GROUP BY otherwise (each call binds "day" as its
    # own parameter, so the SELECT/GROUP BY/ORDER BY copies don't compile as
    # provably the same expression: "column must appear in the GROUP BY clause").
    day_bucket = func.date_trunc("day", SpendLedger.ts)
    burn_down_rows = (
        await session.execute(
            select(day_bucket, func.sum(SpendLedger.cost_usd))
            .where(window)
            .group_by(day_bucket)
            .order_by(day_bucket)
        )
    ).all()
    burn_down = [
        BurnDownPoint(date=day.date().isoformat(), total_usd=_round2(v))
        for day, v in burn_down_rows
    ]

    tok_in, tok_cached = (
        await session.execute(
            select(
                func.coalesce(func.sum(SpendLedger.tok_in), 0),
                func.coalesce(func.sum(SpendLedger.tok_cached), 0),
            ).where(window)
        )
    ).one()
    denom = tok_in + tok_cached
    cache_hit_ratio = round(tok_cached / denom, 4) if denom else 0.0

    return CostSummaryOut(
        total_usd=_round2(total),
        by_dept=by_dept,
        by_agent=by_agent,
        by_model=by_model,
        burn_down=burn_down,
        cache_hit_ratio=cache_hit_ratio,
    )


class AuditRowOut(BaseModel):
    id: int
    ts: dt.datetime
    actor: str
    actor_type: str
    action: str
    entity: str | None
    entity_id: str | None
    trace_id: str | None
    langfuse_url: str | None


def _langfuse_url(settings: Settings, trace_id: str | None) -> str | None:
    if not trace_id:
        return None
    return f"{settings.langfuse_base_url}/project/{settings.langfuse_project_id}/traces/{trace_id}"


@router.get("/audit")
async def list_audit(
    actor: str | None = None,
    action: str | None = None,
    entity: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> list[AuditRowOut]:
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if actor:
        stmt = stmt.where(AuditLog.actor == actor)
    if action:
        stmt = stmt.where(AuditLog.action.contains(action))
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        AuditRowOut(
            id=r.id,
            ts=r.ts,
            actor=r.actor,
            actor_type=r.actor_type,
            action=r.action,
            entity=r.entity,
            entity_id=r.entity_id,
            trace_id=r.trace_id,
            langfuse_url=_langfuse_url(settings, r.trace_id),
        )
        for r in rows
    ]

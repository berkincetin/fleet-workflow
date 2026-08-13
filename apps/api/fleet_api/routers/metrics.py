"""Prometheus scrape endpoint (task 7.4). Unauthenticated by convention, same
as every standard Prometheus exporter — the payload is counters/histograms/
gauges, never request/response bodies or credentials.

Two gauge families are recomputed fresh on every scrape rather than pushed
incrementally, since both are cheap aggregate reads and Prometheus already
polls on a fixed interval (typically 15s):
- dept daily spend + trailing-7-day average, feeding the §5 cost-anomaly
  alert rule (dept daily spend > 3x its 7-day average);
- arq's ingest queue depth (ZCARD of its default sorted-set key), feeding
  the queue-depth alert rule.
"""

from __future__ import annotations

import datetime as dt

import core.metrics as _core_metrics  # noqa: F401 (registers BUDGET_SOFT_LIMIT_TOTAL)
import redis.asyncio as redis
from arq.constants import default_queue_name
from fastapi import APIRouter, Depends, Response
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.metrics import (
    DEPT_AVG_DAILY_SPEND_7D_USD,
    DEPT_DAILY_SPEND_USD,
    QUEUE_DEPTH,
)
from fleet_api.models import SpendLedger
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["metrics"])


async def _refresh_cost_anomaly_gauges(session: AsyncSession) -> None:
    now = dt.datetime.now(dt.UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - dt.timedelta(days=7)

    today_rows = (
        await session.execute(
            select(SpendLedger.dept_id, func.sum(SpendLedger.cost_usd))
            .where(SpendLedger.ts >= today_start, SpendLedger.dept_id.is_not(None))
            .group_by(SpendLedger.dept_id)
        )
    ).all()
    for dept_id, total in today_rows:
        DEPT_DAILY_SPEND_USD.labels(dept_id=dept_id).set(float(total))

    week_rows = (
        await session.execute(
            select(SpendLedger.dept_id, func.sum(SpendLedger.cost_usd))
            .where(SpendLedger.ts >= week_start, SpendLedger.dept_id.is_not(None))
            .group_by(SpendLedger.dept_id)
        )
    ).all()
    for dept_id, total in week_rows:
        DEPT_AVG_DAILY_SPEND_7D_USD.labels(dept_id=dept_id).set(float(total) / 7)


def get_ingest_redis(settings: Settings = Depends(get_settings)) -> redis.Redis:  # noqa: B008
    return redis.from_url(settings.ingest_redis_url)


async def _refresh_queue_depth_gauge(client: redis.Redis) -> None:
    depth = await client.zcard(default_queue_name)
    QUEUE_DEPTH.labels(queue="ingest").set(depth)


@router.get("/metrics")
async def metrics(
    session: AsyncSession = Depends(get_session),  # noqa: B008
    ingest_redis: redis.Redis = Depends(get_ingest_redis),  # noqa: B008
) -> Response:
    await _refresh_cost_anomaly_gauges(session)
    try:
        await _refresh_queue_depth_gauge(ingest_redis)
    finally:
        await ingest_redis.aclose()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

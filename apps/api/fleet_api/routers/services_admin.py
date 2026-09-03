"""Admin -> Services: live health of the local stack (task 13.3, TRD §12).

Closes the long-deferred 7.3 "System health (queues, workers, provider status)"
screen. Every card is probed for real at request time — there is no cached or
declared status here, because the one question this screen answers is "is it up
*right now*".

Two rules shape the API:

1. **Credentials are masked in the list response, always.** `GET /v1/admin/services`
   never carries a usable secret, whoever the caller is. Plaintext lives behind
   a separate, explicitly-invoked `POST .../reveal` that additionally requires
   the caller to actually hold the `platform_admin` role — not merely the
   MANAGE_PLATFORM permission that gates the rest of admin. Values come from
   the process environment; nothing here is committed.
2. **A dead service degrades its own card, nothing else.** Probes run
   concurrently and every failure mode is caught and turned into a `down`
   status, so a stopped container cannot 500 the page (an AC of this task).
"""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlsplit, urlunsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.rbac import Permission, require_permission
from fleet_api.services_catalog import (
    CATALOG,
    CATALOG_BY_NAME,
    ProbeKind,
    ServiceSpec,
    mask_secret,
)
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/admin/services", tags=["admin:services"])

_PROBE_TIMEOUT_SECONDS = 2.5

#: n8n queue-mode workers pull from Redis DB 2 (compose: QUEUE_BULL_REDIS_DB).
_N8N_REDIS_DB = 2
#: Bull's pending-jobs list for n8n's default queue name.
_N8N_WAIT_KEY = "bull:jobs:wait"
#: arq's default queue name (fleet_rag.ingest.worker.WorkerSettings leaves it
#: at the default) and the heartbeat key its worker refreshes while alive.
_ARQ_QUEUE_KEY = "arq:queue"
_ARQ_HEALTH_KEY = "arq:queue:health-check"


class CredentialOut(BaseModel):
    label: str
    username: str | None = None
    #: Masked form. The plaintext is only ever returned by the reveal endpoint.
    secret_masked: str | None = None


class ServiceOut(BaseModel):
    name: str
    group: str
    url: str
    optional: bool
    status: str  # "healthy" | "down" | "unknown"
    detail: str | None = None
    latency_ms: int | None = None
    queue_depth: int | None = None
    credentials: list[CredentialOut] = []
    has_credentials: bool = False


class ServicesOut(BaseModel):
    services: list[ServiceOut]
    healthy: int
    down: int


class ProbeResult(BaseModel):
    status: str
    detail: str | None = None
    latency_ms: int | None = None


def _with_db(url: str, db: int) -> str:
    """Same Redis URL, different database index."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{db}", parts.query, parts.fragment))


async def _probe_http(url: str) -> ProbeResult:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_SECONDS) as client:
            resp = await client.get(url)
    except httpx.HTTPError as exc:
        return ProbeResult(status="down", detail=type(exc).__name__)
    latency = int((time.monotonic() - start) * 1000)
    # 401/403 means the service is up and merely refusing an unauthenticated
    # probe (n8n's REST API, Grafana with anonymous access off) — that is a
    # healthy service, not a down one.
    if resp.status_code < 400 or resp.status_code in (401, 403):
        return ProbeResult(status="healthy", latency_ms=latency)
    return ProbeResult(status="down", detail=f"HTTP {resp.status_code}", latency_ms=latency)


async def _probe_postgres(session: AsyncSession) -> ProbeResult:
    start = time.monotonic()
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — a dead DB must not 500 the page
        return ProbeResult(status="down", detail=type(exc).__name__)
    return ProbeResult(status="healthy", latency_ms=int((time.monotonic() - start) * 1000))


async def _probe_redis(url: str) -> ProbeResult:
    from redis.asyncio import Redis

    start = time.monotonic()
    client = Redis.from_url(url, socket_connect_timeout=_PROBE_TIMEOUT_SECONDS)
    try:
        await client.ping()
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(status="down", detail=type(exc).__name__)
    finally:
        await client.aclose()
    return ProbeResult(status="healthy", latency_ms=int((time.monotonic() - start) * 1000))


async def _probe_arq(url: str) -> tuple[ProbeResult, int | None]:
    """arq worker heartbeat + queued-job count.

    The worker runs on the host rather than in compose, so `down` here is a
    normal dev state (the spec marks it optional). The heartbeat key is written
    by a live worker and expires on its own, which makes its presence — not the
    queue depth — the liveness signal.
    """
    from redis.asyncio import Redis

    client = Redis.from_url(url, socket_connect_timeout=_PROBE_TIMEOUT_SECONDS)
    try:
        alive = await client.exists(_ARQ_HEALTH_KEY)
        depth = await client.zcard(_ARQ_QUEUE_KEY)
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(status="unknown", detail=type(exc).__name__), None
    finally:
        await client.aclose()
    status = "healthy" if alive else "down"
    return ProbeResult(status=status, detail=None if alive else "no worker heartbeat"), int(depth)


async def _n8n_queue_depth(url: str) -> int | None:
    from redis.asyncio import Redis

    client = Redis.from_url(url, socket_connect_timeout=_PROBE_TIMEOUT_SECONDS)
    try:
        return int(await client.llen(_N8N_WAIT_KEY))
    except Exception:  # noqa: BLE001
        return None
    finally:
        await client.aclose()


async def _probe(spec: ServiceSpec, settings: Settings, session: AsyncSession) -> ServiceOut:
    queue_depth: int | None = None

    if spec.probe is ProbeKind.POSTGRES:
        result = await _probe_postgres(session)
    elif spec.probe is ProbeKind.REDIS:
        result = await _probe_redis(settings.redis_url)
    elif spec.probe is ProbeKind.ARQ:
        result, queue_depth = await _probe_arq(settings.ingest_redis_url)
    else:
        result = await _probe_http(spec.effective_probe_url())
        if spec.name == "n8n-worker":
            queue_depth = await _n8n_queue_depth(_with_db(settings.redis_url, _N8N_REDIS_DB))

    credentials = [
        CredentialOut(
            label=cred.label,
            username=cred.username(),
            secret_masked=mask_secret(cred.secret()),
        )
        for cred in spec.credentials
    ]

    return ServiceOut(
        name=spec.name,
        group=spec.group,
        url=spec.url,
        optional=spec.optional,
        status=result.status,
        detail=result.detail,
        latency_ms=result.latency_ms,
        queue_depth=queue_depth,
        credentials=credentials,
        has_credentials=bool(credentials),
    )


@router.get("")
async def list_services(
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ServicesOut:
    """Live status of every service in the catalog. Secrets are masked here
    unconditionally — see the module docstring."""
    # Postgres shares the request's session, so it is probed on its own rather
    # than inside the gather (a single AsyncSession is not concurrency-safe).
    pg_specs = [s for s in CATALOG if s.probe is ProbeKind.POSTGRES]
    other_specs = [s for s in CATALOG if s.probe is not ProbeKind.POSTGRES]

    pg_results = [await _probe(spec, settings, session) for spec in pg_specs]
    other_results = await asyncio.gather(
        *(_probe(spec, settings, session) for spec in other_specs)
    )

    by_name = {r.name: r for r in [*pg_results, *other_results]}
    services = [by_name[s.name] for s in CATALOG]

    return ServicesOut(
        services=services,
        healthy=sum(1 for s in services if s.status == "healthy"),
        down=sum(1 for s in services if s.status == "down" and not s.optional),
    )


class RevealedCredentialOut(BaseModel):
    label: str
    username: str | None = None
    secret: str | None = None


class RevealOut(BaseModel):
    name: str
    credentials: list[RevealedCredentialOut]


@router.post("/{name}/reveal")
async def reveal_credentials(
    name: str,
    current: CurrentUser = Depends(get_current_user),  # noqa: B008
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
) -> RevealOut:
    """Plaintext dev credentials for one service — an explicit, separately
    audited action (AuditMiddleware records the POST), not something the page
    load hands out.

    The extra `platform_admin` role check is deliberate belt-and-braces: it
    keeps the reveal tied to that one role even if MANAGE_PLATFORM is ever
    granted to another role in `rbac.py`.
    """
    if "platform_admin" not in current.roles:
        raise HTTPException(status_code=403, detail="reveal requires the platform_admin role")

    spec = CATALOG_BY_NAME.get(name)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown service: {name}")

    return RevealOut(
        name=spec.name,
        credentials=[
            RevealedCredentialOut(
                label=cred.label, username=cred.username(), secret=cred.secret()
            )
            for cred in spec.credentials
        ],
    )

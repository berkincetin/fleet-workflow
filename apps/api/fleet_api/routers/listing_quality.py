"""Listing Quality run trigger (task 11.1, dept scenario 06).

`POST /v1/listing-quality/runs` runs one listing (photo base64 + description +
price + segment) through the vision check and, if flagged, records the flags via
the mock `listings.flag` tool (write:internal) — a supervised, flag-only action,
so unlike the invoice/dev agents there is no HITL interrupt: flagging into the
internal review queue is not a write:external side effect.

`shadow` mode (default in the 2-week rollout, dept scenario 06) computes the
flags but does NOT call listings.flag — the flags are returned/logged only, so
they can be compared against reviewer decisions without being surfaced.

Reachable by a Keycloak human with MANAGE_AGENTS or a Fleet API key with the
`listing_intake` scope — the n8n new-listing webhook path (no Keycloak session),
same programmatic-access leg as invoice_intake.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from fleet_api.db import get_session
from fleet_api.rbac import Permission
from fleet_api.service_auth import require_user_or_service_scope
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/listing-quality", tags=["listing-quality"])

LISTING_QUALITY_AGENT_NAME = "listing_quality"


class RunIn(BaseModel):
    listing_id: str
    image_base64: str
    description: str
    price: float
    segment: str
    currency: str = "TRY"
    shadow: bool = True  # default shadow mode (flags logged, not queued)


class RunOut(BaseModel):
    run_id: str
    status: str  # "flagged" | "clean" | "shadow_flagged" | "blocked"
    flags: list[dict[str, str]]
    detail: dict[str, Any]


class _ShadowFlag:
    """A listings.flag stand-in that records nothing — shadow mode never queues
    a flag into the human review surface (dept scenario 06 rollout)."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def flag(
        self, *, listing_id: str, codes: list[str], reasons: list[str]
    ) -> dict[str, Any]:
        self.calls.append({"listing_id": listing_id, "codes": codes})
        return {"status": "shadow_not_queued"}


@router.post("/runs", status_code=201)
async def start_run(
    body: RunIn,
    _: object = Depends(  # noqa: B008
        require_user_or_service_scope(Permission.MANAGE_AGENTS, "listing_intake")
    ),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunOut:
    from agents.listing_quality.graph import build_listing_quality_graph
    from core.llm.factory import build_client
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.listings import build_listings_server
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool
    from langgraph.checkpoint.memory import InMemorySaver

    llm_client = await build_client()

    class _PriceIndex:
        """Reference band via governed read-only SQL over the price-index view.

        The segment is validated against the view's own rows (it is used only in
        a WHERE literal after passing the pg_ro SELECT-only guardrail), so a
        crafted segment string cannot become anything but a filter value against
        a read-only role."""

        def __init__(self) -> None:
            self._pg = PgReadOnlyTool(
                runner=build_default_runner(),
                allowlisted_tables={"fixture_price_index"},
            )

        async def reference_band(self, *, segment: str) -> dict[str, Any] | None:
            safe = segment.replace("'", "''")
            rows = await self._pg.query(
                "SELECT band_low, band_high, band_median, currency "
                f"FROM fixture_price_index WHERE segment = '{safe}'"
            )
            if not rows:
                return None
            r = rows[0]
            return {
                "low": r["band_low"], "high": r["band_high"],
                "median": r["band_median"], "currency": r["currency"],
            }

    if body.shadow:
        flag_tool: Any = _ShadowFlag()
    else:
        _, flag_tool = build_listings_server(api_key="internal")

    run_id = str(uuid.uuid4())
    # No Postgres checkpointer: this agent has no HITL interrupt/resume (flag-only,
    # runs start-to-finish in one call), so an in-memory saver is sufficient and
    # avoids the Windows ProactorEventLoop/psycopg-async incompatibility that the
    # interrupt-bearing agents route around in routers/approvals.py.
    graph = build_listing_quality_graph(
        vision_client=llm_client,
        price_index=_PriceIndex(),
        listings_flag=flag_tool,
        checkpointer=InMemorySaver(),
    )
    result = await graph.ainvoke(
        {
            "listing_id": body.listing_id, "image_base64": body.image_base64,
            "description": body.description, "price": body.price,
            "currency": body.currency, "segment": body.segment,
        },
        {"configurable": {"thread_id": f"lq-{run_id}"}},
    )

    if result.get("blocked_reason"):
        return RunOut(
            run_id=run_id, status="blocked", flags=[],
            detail={"reason": result["blocked_reason"]},
        )

    verdict = result.get("verdict", {"flags": [], "clean": True})
    flags = verdict["flags"]
    if not flags:
        status = "clean"
    elif body.shadow:
        status = "shadow_flagged"
    else:
        status = "flagged"
    return RunOut(run_id=run_id, status=status, flags=flags, detail={"clean": verdict["clean"]})

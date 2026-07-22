"""Service-to-Fleet-API surface for automations (task 6.1/6.2, TRD §7.1).

Routes here are authenticated by `X-Fleet-Api-Key` (service_auth.py), not a
Keycloak bearer token — this is the "programmatic access" leg n8n workflows
call. `pg-query` wraps the same governed `PgReadOnlyTool` the Analytics agent
uses (task 5.1/5.2): allowlist + DML-block + row-limit + timeout apply
identically whether the caller is an LLM-generated query or an n8n cron job.
"""

from __future__ import annotations

from core.errors import GovernedToolRefusal
from fastapi import APIRouter, Depends, HTTPException
from fleet_api.service_auth import CurrentServiceKey, require_scope
from fleet_mcp.servers.asyncpg_runner import build_default_runner
from fleet_mcp.servers.pg_ro import PgReadOnlyTool
from fleet_mcp.servers.slack import DisallowedChannelError, SlackPostTool, build_default_sender
from pydantic import BaseModel

router = APIRouter(prefix="/v1/service", tags=["service"])

# Same fixture allowlist the Analytics agent's semantic layer knows about
# (task 5.1/5.2) — the weekly-summary automation (6.2) reads from these.
_ALLOWLISTED_TABLES = {"fixture_sales", "fixture_orders"}

# Channels n8n automations may post to (task 6.2's weekly summary posts here).
# Same allowlist-independent-of-risk_class guard dept scenario 03 established
# for the Dev Agent's Slack step (5.3/5.5) — a second, service-key-driven
# caller of slack.post shouldn't get a wider allowlist than an LLM-driven one.
_ALLOWLISTED_CHANNELS = {"#dev-agent", "#weekly-summary"}


class PgQueryIn(BaseModel):
    sql: str


class PgQueryOut(BaseModel):
    rows: list[dict[str, object]]
    row_count: int


def get_pg_ro_tool() -> PgReadOnlyTool:
    return PgReadOnlyTool(runner=build_default_runner(), allowlisted_tables=_ALLOWLISTED_TABLES)


@router.post("/pg-query")
async def pg_query(
    body: PgQueryIn,
    _: CurrentServiceKey = Depends(require_scope("pg_ro")),  # noqa: B008
    tool: PgReadOnlyTool = Depends(get_pg_ro_tool),  # noqa: B008
) -> PgQueryOut:
    try:
        rows = await tool.query(body.sql)
    except GovernedToolRefusal as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PgQueryOut(rows=rows, row_count=len(rows))


class SlackPostIn(BaseModel):
    channel: str
    text: str


def get_slack_tool() -> SlackPostTool:
    return SlackPostTool(sender=build_default_sender(), allowed_channels=_ALLOWLISTED_CHANNELS)


@router.post("/slack-post", status_code=204)
async def slack_post(
    body: SlackPostIn,
    _: CurrentServiceKey = Depends(require_scope("slack_post")),  # noqa: B008
    tool: SlackPostTool = Depends(get_slack_tool),  # noqa: B008
) -> None:
    try:
        await tool.post(channel=body.channel, text=body.text)
    except DisallowedChannelError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

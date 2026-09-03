"""Service-to-Fleet-API surface for automations (task 6.1/6.2, TRD §7.1).

Routes here are authenticated by `X-Fleet-Api-Key` (service_auth.py), not a
Keycloak bearer token — this is the "programmatic access" leg n8n workflows
call. `pg-query` wraps the same governed `PgReadOnlyTool` the Analytics agent
uses (task 5.1/5.2): allowlist + DML-block + row-limit + timeout apply
identically whether the caller is an LLM-generated query or an n8n cron job.
"""

from __future__ import annotations

from core.errors import GovernedToolRefusal
from core.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Request
from fleet_api.db import get_session
from fleet_api.service_auth import CurrentServiceKey, require_scope
from fleet_mcp.servers.asyncpg_runner import build_default_runner
from fleet_mcp.servers.pg_ro import PgReadOnlyTool
from fleet_mcp.servers.slack import DisallowedChannelError, SlackPostTool, build_default_sender
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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


# --- Automation-recipe actions (task 13.4) -------------------------------
#
# The compiled n8n workflow of a recipe only ever POSTs to routes in this
# module, which is what keeps Non-Negotiable Rule 3 true for user-defined
# automations: `email.send` lands in the approval queue here, in code, rather
# than depending on the recipe having been built correctly.

# Same sandbox domains the Dealer Onboarding agent's email tool allows (5.1/12.1)
# — a recipe-driven send must not reach further than an LLM-driven one.
_ALLOWED_EMAIL_DOMAINS = {"fleet.local", "example.com"}

#: The pseudo-agent every recipe-queued approval is filed under. It exists so
#: `approvals.agent_id` (a NOT NULL FK) has a row to point at and so the
#: resume registry can key on it like any other interrupt-producing agent; it
#: is seeded `paused` and never appears as a chat agent.
RECIPE_AGENT_NAME = "automation_recipe"


class AgentRunIn(BaseModel):
    agent: str
    question: str


class AgentRunOut(BaseModel):
    text: str
    trace_id: str


@router.post("/agent-run")
async def agent_run(
    body: AgentRunIn,
    request: Request,
    _: CurrentServiceKey = Depends(require_scope("agent_run")),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AgentRunOut:
    """Run one agent turn from an automation, reusing the exact reply paths the
    chat router uses (RAG-grounded, analytics text-to-SQL, or plain reasoning)
    — an automation must not get a second, differently-governed way to talk to
    an agent."""
    import uuid

    from core.llm.factory import build_client
    from fleet_api.models import Agent
    from fleet_api.routers.chat import (
        ANALYTICS_AGENT_NAME,
        _analytics_reply,
        _assert_agent_may_read_its_collections,
        _rag_reply,
    )
    from sqlalchemy import select

    agent = (
        await session.execute(select(Agent).where(Agent.name == body.agent))
    ).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail=f"unknown agent: {body.agent}")
    if agent.status != "active":
        raise HTTPException(status_code=409, detail=f"agent is {agent.status}")
    await _assert_agent_may_read_its_collections(session, agent)

    llm_client = getattr(request.app.state, "llm_client", None) or await build_client()
    trace_id = str(uuid.uuid4())

    if agent.name == ANALYTICS_AGENT_NAME:
        text_out = await _analytics_reply(
            agent=agent, user_content=body.question, llm_client=llm_client, trace_id=trace_id
        )
    elif agent.collection_ids:
        text_out, _citations = await _rag_reply(
            agent=agent, user_content=body.question, llm_client=llm_client, trace_id=trace_id
        )
    else:
        chunks: list[str] = []
        async for delta in llm_client.reasoning_stream(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": body.question},
            ],
            sensitivity=agent.sensitivity,
            agent_id=str(agent.id),
            trace_id=trace_id,
        ):
            chunks.append(delta)
        text_out = "".join(chunks)

    return AgentRunOut(text=text_out, trace_id=trace_id)


class EmailSendIn(BaseModel):
    to: str
    subject: str
    body: str


class EmailSendOut(BaseModel):
    status: str  # always "queued_for_approval"
    approval_id: int
    run_id: str


@router.post("/email-send", status_code=202)
async def email_send(
    body: EmailSendIn,
    _: CurrentServiceKey = Depends(require_scope("email_send")),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> EmailSendOut:
    """Queue an email for human approval. **Never sends.**

    `email.send` is write:external (TRD §9 names customer email as the
    canonical always-approved case), so the only thing this endpoint can do is
    create the queue entry; the message goes on the wire in the approvals
    router's resume handler, after a person approves it.
    """
    import uuid

    from fleet_api.models import Agent, Approval
    from fleet_mcp.servers.email import is_allowed_recipient
    from sqlalchemy import select

    if not is_allowed_recipient(body.to, _ALLOWED_EMAIL_DOMAINS):
        raise HTTPException(status_code=422, detail=f"recipient not allowed: {body.to!r}")

    agent = (
        await session.execute(select(Agent).where(Agent.name == RECIPE_AGENT_NAME))
    ).scalar_one_or_none()
    if agent is None:
        raise HTTPException(
            status_code=500,
            detail=f"{RECIPE_AGENT_NAME!r} agent row is missing — run `make seed`",
        )

    run_id = str(uuid.uuid4())
    approval = Approval(
        agent_id=agent.id,
        run_id=run_id,
        action="email.send",
        payload={"to": body.to, "subject": body.subject, "body": body.body},
        status="pending",
    )
    session.add(approval)
    await session.commit()
    await session.refresh(approval)
    return EmailSendOut(
        status="queued_for_approval", approval_id=approval.id, run_id=run_id
    )


class NotifyIn(BaseModel):
    title: str
    message: str


@router.post("/notify", status_code=202)
async def notify(
    body: NotifyIn,
    key: CurrentServiceKey = Depends(require_scope("notify")),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, str]:
    """Internal notification: an audit-log entry an operator can find later.

    Deliberately the one recipe action with no outward effect at all — it is
    what a builder reaches for when the automation should leave a trace rather
    than message a person.
    """
    from fleet_api.models import AuditLog

    session.add(
        AuditLog(
            actor=key.name,
            actor_type="service",
            action="automation.notify",
            entity="automation_recipe",
            entity_id=body.title[:255],
        )
    )
    await session.commit()
    get_logger("fleet.automation").info(
        "automation.notify", extra={"fields": {"title": body.title}}
    )
    return {"status": "recorded"}

"""Chat: conversations, SSE-streamed messages, feedback (task 4.3/4.4, TRD §12).

`POST /v1/conversations` creates a thread against an active, non-paused agent.
`POST /v1/conversations/{id}/messages` streams the assistant's reply as
Server-Sent Events, then a `citations` event, then `done` carrying the
persisted message id and trace_id. `POST /v1/messages/{id}/feedback` records a
thumbs up/down and pushes it as a Langfuse score on that message's trace (§6)
— the AC is "lands in Langfuse", not just the DB row.

Three reply paths, chosen per-agent:
- **Analytics (agent.name == "analytics", task 5.2):** agents.analytics.service
  — NL question -> SQL (reasoning tier) -> fleet_mcp.servers.pg_ro governed
  execution (allowlist/DML-block/auto-LIMIT). Not streaming or RAG; the SQL
  and row count are rendered as the reply text so "generated SQL always
  displayed to user" holds on every answer, refusal, and clarification alike.
- **RAG (Support Copilot and any future KB-backed agent, agent.collection_ids
  set):** fleet_rag's answer_query() — embed -> hybrid retrieve -> generate ->
  structural grounding check (TRD §9), the same pipeline task 3.3's
  /v1/rag/query test harness exercises. This is a single non-streaming call
  (the citation-verification retry loop needs the full answer before it can
  validate it), emitted as one `token` event with the complete grounded text,
  then real citations.
- **Plain passthrough (no collections configured):** real upstream token
  streaming via core.llm.client.LLMClient.reasoning_stream (TRD §5 "streaming
  everywhere") — what task 4.3 built and proved the SSE/feedback transport
  contract against; citations are always empty on this path.

fleet_rag is imported lazily inside the handler, not at module scope, matching
the existing avoid-circular-dependency boundary in routers/documents.py and
routers/rag_query.py (fleet-rag's pyproject depends on fleet-api, not the
reverse).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator, Coroutine
from typing import Any

from core.killswitch import KillSwitch
from core.langfuse_client import LangfuseRedactor, LangfuseScorer
from core.llm.client import GatewayError, LLMClient
from core.llm.factory import build_client
from core.logging import get_logger
from core.pii_scrub import scrub
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import Agent, Collection, Conversation, Feedback, Message
from fleet_api.privacy import subject_hash
from fleet_api.rbac import Permission, require_permission
from fleet_api.users import get_or_create_user
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1", tags=["chat"])
chat_logger = get_logger("fleet.chat")

# Fire-and-forget background tasks (Langfuse redaction, task 8.4) need a
# strong reference held somewhere or the event loop may garbage-collect them
# mid-flight (asyncio only holds a weak reference to a bare create_task()
# result) — this set is that reference; each task removes itself on completion.
_background_tasks: set[asyncio.Task[None]] = set()


def _spawn_background(coro: Coroutine[Any, Any, None]) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def get_killswitch(settings: Settings = Depends(get_settings)) -> KillSwitch:  # noqa: B008
    return KillSwitch(Redis.from_url(settings.redis_url, decode_responses=True))


def get_langfuse_scorer(settings: Settings = Depends(get_settings)) -> LangfuseScorer:  # noqa: B008
    return LangfuseScorer(
        base_url=settings.langfuse_base_url,
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
    )


def get_langfuse_redactor(settings: Settings = Depends(get_settings)) -> LangfuseRedactor:  # noqa: B008
    return LangfuseRedactor(
        base_url=settings.langfuse_base_url,
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
    )


class AgentSummaryOut(BaseModel):
    id: int
    name: str
    status: str

    model_config = {"from_attributes": True}


@router.get("/agents")
async def list_chat_agents(
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[AgentSummaryOut]:
    """Active agents any CHAT-permitted user (TRD §7.1: every role) may start a
    conversation with — unlike /v1/admin/agents, no MANAGE_AGENTS required."""
    rows = (
        await session.execute(select(Agent).where(Agent.status == "active").order_by(Agent.id))
    ).scalars().all()
    return [AgentSummaryOut.model_validate(r) for r in rows]


class ConversationIn(BaseModel):
    agent_id: int


class ConversationOut(BaseModel):
    id: int
    agent_id: int
    user_id: int

    model_config = {"from_attributes": True}


@router.post("/conversations", status_code=201)
async def create_conversation(
    body: ConversationIn,
    current: CurrentUser = Depends(get_current_user),  # noqa: B008
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ConversationOut:
    agent = await session.get(Agent, body.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")

    user = await get_or_create_user(session, kc_sub=current.sub)
    row = Conversation(
        agent_id=agent.id, user_id=user.id, subject_hash=subject_hash(current.sub)
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return ConversationOut.model_validate(row)


class MessageIn(BaseModel):
    content: str


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _assert_agent_may_read_its_collections(session: AsyncSession, agent: Agent) -> None:
    """§8: agents cannot read collections above their own sensitivity level."""
    from core.llm.routing import Sensitivity

    if not agent.collection_ids:
        return
    agent_level = Sensitivity.parse(agent.sensitivity)
    rows = (
        await session.execute(
            select(Collection).where(Collection.id.in_(agent.collection_ids))
        )
    ).scalars().all()
    for collection in rows:
        if Sensitivity.parse(collection.sensitivity) > agent_level:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"agent sensitivity {agent.sensitivity!r} cannot read collection "
                    f"{collection.name!r} (sensitivity {collection.sensitivity!r})"
                ),
            )


ANALYTICS_AGENT_NAME = "analytics"


async def _analytics_reply(
    *, agent: Agent, user_content: str, llm_client: LLMClient, trace_id: str
) -> str:
    """Text-to-SQL reply for the Analytics agent (task 5.2, dept scenario 02).

    Not a RAG path — no collections/citations. Renders the generated SQL and
    the returned rows as the message text so "generated SQL always displayed
    to user" (the department scenario's guardrail) holds for every answer,
    not just successful ones being silently correct.
    """
    from agents.analytics.semantic_layer import DEFAULT_SEMANTIC_LAYER
    from agents.analytics.service import AnalyticsClarification, AnalyticsRefusal, ask_analytics
    from fleet_mcp.servers.asyncpg_runner import build_default_runner
    from fleet_mcp.servers.pg_ro import PgReadOnlyTool

    pg_tool = PgReadOnlyTool(
        runner=build_default_runner(),
        allowlisted_tables=DEFAULT_SEMANTIC_LAYER.allowlisted_tables(),
    )
    try:
        result = await ask_analytics(
            question=user_content,
            semantic_layer=DEFAULT_SEMANTIC_LAYER,
            llm_client=llm_client,
            pg_tool=pg_tool,
            sensitivity=agent.sensitivity,
            agent_id=str(agent.id),
            trace_id=trace_id,
        )
    except AnalyticsClarification as exc:
        return str(exc)
    except AnalyticsRefusal as exc:
        return f"I can't run that query: {exc}"

    return f"```sql\n{result.sql}\n```\n\n{len(result.rows)} row(s) returned."


async def _rag_reply(
    *, agent: Agent, user_content: str, llm_client: LLMClient, trace_id: str
) -> tuple[str, list[dict[str, Any]]]:
    """Grounded RAG answer over agent.collection_ids (task 4.4)."""
    from fleet_rag.query.retrieve import Hit
    from fleet_rag.query.service import AgentQueryConfig, answer_query
    from fleet_rag.store.qdrant_store import collection_name, qdrant_client_from_env, search_hybrid

    qdrant = qdrant_client_from_env()
    collection_names = [collection_name(cid) for cid in agent.collection_ids]

    def _searcher(
        *, query_vector: list[float], top_k: int, keyword: str | None = None
    ) -> list[Hit]:
        hits: list[Hit] = []
        for qname in collection_names:
            points = search_hybrid(
                qdrant, qname, query_vector=query_vector, top_k=top_k, keyword=keyword
            )
            hits.extend(
                Hit(
                    id=str(p.id),
                    score=p.score,
                    document_id=p.payload["document_id"],
                    chunk_ref=p.payload["content_sha256"],
                    content=p.payload["content"],
                    redacted=p.payload.get("redacted", False),
                )
                for p in points
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    answer = await answer_query(
        question=user_content,
        searcher=_searcher,
        embed_client=llm_client,
        reasoning_client=llm_client,
        config=AgentQueryConfig(top_k=5),
        sensitivity=agent.sensitivity,
        agent_id=str(agent.id),
        trace_id=trace_id,
    )
    citations = [
        {"chunk_ref": c.chunk_ref, "document_id": c.document_id} for c in answer.citations
    ]
    return answer.text, citations


async def _stream_reply(
    *,
    session: AsyncSession,
    conversation: Conversation,
    agent: Agent,
    user_content: str,
    llm_client: LLMClient,
    langfuse_redactor: LangfuseRedactor,
) -> AsyncIterator[str]:
    trace_id = str(uuid.uuid4())

    # TRD §8: "Chat inputs scanned lightweight; detected identifiers masked in
    # logs/traces always" — independent of the agent's sensitivity tier. A
    # masked copy goes to our own structured log; the unredacted content still
    # goes to the model itself (it needs the real content to answer), but a
    # PII-bearing turn also gets litellm's own redaction switch so Langfuse
    # never receives the raw prompt/response for it.
    pii = scrub(user_content)
    chat_logger.info(
        "chat.message.received",
        extra={"fields": {"conversation_id": conversation.id, "role": "user", "content": pii.text}},
    )
    redact_langfuse = pii.found

    user_message = Message(conv_id=conversation.id, role="user", content=user_content)
    session.add(user_message)
    await session.flush()

    text = ""
    citations: list[dict[str, Any]] = []

    if agent.name == ANALYTICS_AGENT_NAME:
        try:
            text = await _analytics_reply(
                agent=agent, user_content=user_content, llm_client=llm_client, trace_id=trace_id
            )
        except GatewayError as exc:
            yield _sse("error", {"detail": str(exc)})
            await session.commit()
            return
        yield _sse("token", {"delta": text})
    elif agent.collection_ids:
        try:
            text, citations = await _rag_reply(
                agent=agent, user_content=user_content, llm_client=llm_client, trace_id=trace_id
            )
        except GatewayError as exc:
            yield _sse("error", {"detail": str(exc)})
            await session.commit()
            return
        yield _sse("token", {"delta": text})
    else:
        try:
            async for delta in llm_client.reasoning_stream(
                [{"role": "system", "content": "You are a helpful assistant."},
                 {"role": "user", "content": user_content}],
                sensitivity=agent.sensitivity,
                agent_id=str(agent.id),
                user_id=str(conversation.user_id),
                trace_id=trace_id,
                redact_langfuse=redact_langfuse,
            ):
                text += delta
                yield _sse("token", {"delta": delta})
        except GatewayError as exc:
            yield _sse("error", {"detail": str(exc)})
            await session.commit()
            return

    yield _sse("citations", {"citations": citations})

    assistant_message = Message(
        conv_id=conversation.id,
        role="assistant",
        content=text,
        tool_trace={"citations": citations},
        trace_id=trace_id,
    )
    session.add(assistant_message)
    await session.commit()
    await session.refresh(assistant_message)

    if redact_langfuse:
        # Fire-and-forget: Langfuse ingestion is async and litellm's own
        # callback has almost certainly already written the raw trace by the
        # time we get control back here, so this best-effort overwrite runs
        # after it without adding latency to the SSE response (task 8.4).
        _spawn_background(langfuse_redactor.redact_trace(trace_id=trace_id))

    yield _sse("done", {"message_id": assistant_message.id, "trace_id": trace_id})


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    body: MessageIn,
    request: Request,
    current: CurrentUser = Depends(get_current_user),  # noqa: B008
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    killswitch: KillSwitch = Depends(get_killswitch),  # noqa: B008
    langfuse_redactor: LangfuseRedactor = Depends(get_langfuse_redactor),  # noqa: B008
) -> StreamingResponse:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")

    user = await get_or_create_user(session, kc_sub=current.sub)
    if conversation.user_id != user.id:
        raise HTTPException(status_code=403, detail="not your conversation")

    agent = await session.get(Agent, conversation.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")

    if agent.status == "paused" or await killswitch.is_agent_paused(agent.name):
        raise HTTPException(status_code=409, detail="agent is paused")

    await _assert_agent_may_read_its_collections(session, agent)

    llm_client = getattr(request.app.state, "llm_client", None) or await build_client()

    return StreamingResponse(
        _stream_reply(
            session=session,
            conversation=conversation,
            agent=agent,
            user_content=body.content,
            llm_client=llm_client,
            langfuse_redactor=langfuse_redactor,
        ),
        media_type="text/event-stream",
    )


class FeedbackIn(BaseModel):
    score: int  # 1 (up) | -1 (down)
    reason: str | None = None


@router.post("/messages/{message_id}/feedback", status_code=201)
async def submit_feedback(
    message_id: int,
    body: FeedbackIn,
    _: object = Depends(require_permission(Permission.CHAT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    scorer: LangfuseScorer = Depends(get_langfuse_scorer),  # noqa: B008
) -> dict[str, int]:
    if body.score not in (1, -1):
        raise HTTPException(status_code=422, detail="score must be 1 or -1")

    message = await session.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="message not found")

    row = Feedback(message_id=message_id, score=body.score, reason=body.reason)
    session.add(row)
    await session.commit()
    await session.refresh(row)

    if message.trace_id:
        await scorer.push_score(
            trace_id=message.trace_id, score=body.score, reason=body.reason
        )

    return {"id": row.id}

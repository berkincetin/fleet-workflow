"""Chat: conversations, SSE-streamed messages, feedback (task 4.3, TRD §12).

`POST /v1/conversations` creates a thread against an active, non-paused agent.
`POST /v1/conversations/{id}/messages` streams the assistant's reply as
Server-Sent Events: one `token` event per text delta (real upstream streaming
via core.llm.client.LLMClient.reasoning_stream, TRD §5 "streaming everywhere"),
then a `citations` event, then `done` carrying the persisted message id and
trace_id. `POST /v1/messages/{id}/feedback` records a thumbs up/down and pushes
it as a Langfuse score on that message's trace (§6) — the AC is "lands in
Langfuse", not just the DB row.

This endpoint calls the gateway client directly (RAG-less passthrough) rather
than through core.graph — task 4.4 wires the real Support Copilot agent
(guardrails/citations/semantic-cache/kill-switch, all built in 4.1/4.2) in as
this endpoint's model; 4.3 proves the SSE/citation/feedback transport contract
the UI is built against.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from core.killswitch import KillSwitch
from core.langfuse_client import LangfuseScorer
from core.llm.client import GatewayError, LLMClient
from core.llm.factory import build_client
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import Agent, Conversation, Feedback, Message, User
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1", tags=["chat"])


def get_killswitch(settings: Settings = Depends(get_settings)) -> KillSwitch:  # noqa: B008
    return KillSwitch(Redis.from_url(settings.redis_url, decode_responses=True))


def get_langfuse_scorer(settings: Settings = Depends(get_settings)) -> LangfuseScorer:  # noqa: B008
    return LangfuseScorer(
        base_url=settings.langfuse_base_url,
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
    )


async def _get_or_create_user(session: AsyncSession, current: CurrentUser) -> User:
    """First-login provisioning: a verified Keycloak principal always gets an
    internal users row, rather than requiring every user to be pre-seeded."""
    row = (
        await session.execute(select(User).where(User.kc_sub == current.sub))
    ).scalar_one_or_none()
    if row is not None:
        return row
    row = User(kc_sub=current.sub, email_hash="", display_name=current.sub)
    session.add(row)
    await session.flush()
    return row


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

    user = await _get_or_create_user(session, current)
    row = Conversation(agent_id=agent.id, user_id=user.id)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return ConversationOut.model_validate(row)


class MessageIn(BaseModel):
    content: str


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _stream_reply(
    *,
    session: AsyncSession,
    conversation: Conversation,
    agent: Agent,
    user_content: str,
    llm_client: LLMClient,
) -> AsyncIterator[str]:
    trace_id = str(uuid.uuid4())

    user_message = Message(conv_id=conversation.id, role="user", content=user_content)
    session.add(user_message)
    await session.flush()

    text = ""
    try:
        async for delta in llm_client.reasoning_stream(
            [{"role": "system", "content": "You are a helpful assistant."},
             {"role": "user", "content": user_content}],
            sensitivity=agent.sensitivity,
            agent_id=str(agent.id),
            user_id=str(conversation.user_id),
            trace_id=trace_id,
        ):
            text += delta
            yield _sse("token", {"delta": delta})
    except GatewayError as exc:
        yield _sse("error", {"detail": str(exc)})
        await session.commit()
        return

    citations: list[dict[str, Any]] = []
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
) -> StreamingResponse:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")

    user = await _get_or_create_user(session, current)
    if conversation.user_id != user.id:
        raise HTTPException(status_code=403, detail="not your conversation")

    agent = await session.get(Agent, conversation.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")

    if agent.status == "paused" or await killswitch.is_agent_paused(agent.name):
        raise HTTPException(status_code=409, detail="agent is paused")

    llm_client = getattr(request.app.state, "llm_client", None) or await build_client()

    return StreamingResponse(
        _stream_reply(
            session=session,
            conversation=conversation,
            agent=agent,
            user_content=body.content,
            llm_client=llm_client,
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

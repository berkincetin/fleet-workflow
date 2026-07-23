"""Agent registry CRUD + kill switches (task 4.2, TRD §11, §9).

CRUD requires MANAGE_AGENTS (builder/dept_admin/platform_admin per §7.1's
"Create/edit agents (dept)" row). Pause/resume writes straight through to the
runtime's KillSwitch (Redis) so the 5s-cached enforcement in core.graph sees
it on the very next check — the DB `status` column is the durable record an
Admin UI list can read; Redis is the low-latency gate the runtime actually
polls. Global read-only is a platform-wide action (MANAGE_PLATFORM only).
"""

from __future__ import annotations

from core.killswitch import KillSwitch
from fastapi import APIRouter, Depends, HTTPException
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import Agent
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/admin/agents", tags=["admin:agents"])

_VALID_SENSITIVITY = {"public", "internal", "confidential", "pii"}


def get_killswitch(settings: Settings = Depends(get_settings)) -> KillSwitch:  # noqa: B008
    return KillSwitch(Redis.from_url(settings.redis_url, decode_responses=True))


class AgentIn(BaseModel):
    name: str
    dept_id: int | None = None
    reasoning_model: str = "reasoning"
    utility_model: str = "utility"
    sensitivity: str = "internal"
    guardrail_policy_id: str | None = None
    semantic_cache: bool = False
    semantic_cache_threshold: float = Field(default=0.95, ge=0, le=1)
    max_context_tokens: int = Field(default=8000, gt=0)
    collection_ids: list[int] = Field(default_factory=list)


class AgentOut(BaseModel):
    id: int
    name: str
    dept_id: int | None
    status: str
    reasoning_model: str
    utility_model: str
    sensitivity: str
    guardrail_policy_id: str | None
    semantic_cache: bool
    semantic_cache_threshold: float
    max_context_tokens: int
    collection_ids: list[int]

    model_config = {"from_attributes": True}


def _validate(body: AgentIn) -> None:
    if body.sensitivity not in _VALID_SENSITIVITY:
        raise HTTPException(status_code=422, detail=f"unknown sensitivity: {body.sensitivity}")


@router.post("", status_code=201)
async def create_agent(
    body: AgentIn,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AgentOut:
    _validate(body)
    existing = (
        await session.execute(select(Agent).where(Agent.name == body.name))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="agent name already exists")

    row = Agent(**body.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return AgentOut.model_validate(row)


@router.get("")
async def list_agents(
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[AgentOut]:
    rows = (await session.execute(select(Agent).order_by(Agent.id))).scalars().all()
    return [AgentOut.model_validate(r) for r in rows]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AgentOut:
    row = await session.get(Agent, agent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return AgentOut.model_validate(row)


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: int,
    body: AgentIn,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AgentOut:
    _validate(body)
    row = await session.get(Agent, agent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return AgentOut.model_validate(row)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    row = await session.get(Agent, agent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found")
    await session.delete(row)
    await session.commit()


@router.post("/{agent_id}/pause", status_code=204)
async def pause_agent(
    agent_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    killswitch: KillSwitch = Depends(get_killswitch),  # noqa: B008
) -> None:
    """Kill switch (§9): instant, cached <=5s in the runtime (core.killswitch)."""
    row = await session.get(Agent, agent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found")
    row.status = "paused"
    await session.commit()
    await killswitch.pause_agent(row.name)


@router.post("/{agent_id}/resume", status_code=204)
async def resume_agent(
    agent_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_AGENTS)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    killswitch: KillSwitch = Depends(get_killswitch),  # noqa: B008
) -> None:
    row = await session.get(Agent, agent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found")
    row.status = "active"
    await session.commit()
    await killswitch.resume_agent(row.name)


class ReadOnlyIn(BaseModel):
    enabled: bool


class ReadOnlyOut(BaseModel):
    enabled: bool


@router.get("/global/read-only")
async def get_global_read_only(
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    killswitch: KillSwitch = Depends(get_killswitch),  # noqa: B008
) -> ReadOnlyOut:
    """Current state of the global kill switch (task 6.5.3) — lets the Admin
    UI render the toggle's initial position without assuming it's off."""
    return ReadOnlyOut(enabled=await killswitch.is_global_read_only())


@router.put("/global/read-only", status_code=204)
async def set_global_read_only(
    body: ReadOnlyIn,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    killswitch: KillSwitch = Depends(get_killswitch),  # noqa: B008
) -> None:
    """Global kill switch (§9): blocks every write:* tool call platform-wide."""
    await killswitch.set_global_read_only(body.enabled)

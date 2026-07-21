"""Admin model registry CRUD (task 2.2, TRD §4.1).

POST adds a model, runs the connectivity/capability smoke test through the
LiteLLM proxy, and stores the result on the row (§4.1 add-a-model flow). All
routes require MANAGE_PLATFORM (platform_admin) — clearance changes and model
management are platform-admin actions recorded in audit (§4.2). The route-level
AuditMiddleware already emits an audit row per request carrying the trace_id.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.models import Model
from fleet_api.rbac import Permission, require_permission
from fleet_api.registry import ModelDraft, build_model_row, evaluate_smoke
from fleet_api.registry_probe import probe_model
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/admin/models", tags=["admin:models"])


class ModelIn(BaseModel):
    """Add-a-model form payload (§4.1)."""

    name: str
    provider: str
    litellm_model_id: str
    input_price_per_1k: float = Field(ge=0)
    output_price_per_1k: float = Field(ge=0)
    context_window: int = Field(gt=0)
    capabilities: list[str] = Field(default_factory=list)
    max_output_tokens: int = Field(gt=0)
    sensitivity_clearance: str
    endpoint: str | None = None
    cached_input_price: float | None = None
    region: str | None = None

    def to_draft(self) -> ModelDraft:
        return ModelDraft(**self.model_dump())


class ModelOut(BaseModel):
    id: int
    name: str
    provider: str
    litellm_model_id: str
    sensitivity_clearance: str
    status: str
    smoke_status: str
    smoke_detail: str | None
    smoke_latency_ms: int | None

    model_config = {"from_attributes": True}


def _out(row: Model) -> ModelOut:
    return ModelOut.model_validate(row)


@router.post("", status_code=201)
async def add_model(
    body: ModelIn,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ModelOut:
    """Insert a model, run its smoke test, and persist the result on the row."""
    draft = body.to_draft()
    try:
        fields = build_model_row(draft)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    row = Model(**fields)
    session.add(row)
    await session.flush()  # assign id; keep the row pending until smoke resolves

    probe = await probe_model(
        draft,
        proxy_base_url=settings.litellm_base_url,
        master_key=settings.litellm_master_key,
    )
    status, smoke_fields = evaluate_smoke(draft, probe)
    row.status = status
    for key, value in smoke_fields.items():
        setattr(row, key, value)
    row.smoke_at = dt.datetime.now(dt.UTC)

    await session.commit()
    await session.refresh(row)
    return _out(row)


@router.get("")
async def list_models(
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[ModelOut]:
    rows = (await session.execute(select(Model).order_by(Model.id))).scalars().all()
    return [_out(r) for r in rows]


@router.get("/{model_id}")
async def get_model(
    model_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ModelOut:
    row = await session.get(Model, model_id)
    if row is None:
        raise HTTPException(status_code=404, detail="model not found")
    return _out(row)


@router.delete("/{model_id}", status_code=204)
async def delete_model(
    model_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    row = await session.get(Model, model_id)
    if row is None:
        raise HTTPException(status_code=404, detail="model not found")
    await session.delete(row)
    await session.commit()

"""Admin API-key issuance/list/revoke (task 6.1, TRD §7.1/§11).

Issuance is a platform-wide credential-control action (same class as model
registry/global budgets in the §7.1 matrix), so every route requires
MANAGE_PLATFORM. The raw key is returned exactly once, in the POST response —
it is never retrievable again, matching "hashed, scoped, expiring" (only the
hash is persisted).
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.api_keys import generate_key, hash_key
from fleet_api.auth import CurrentUser
from fleet_api.db import get_session
from fleet_api.models import ApiKey
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/admin/api-keys", tags=["admin:api-keys"])


class ApiKeyIn(BaseModel):
    name: str
    scopes: list[str] = Field(default_factory=list)
    dept_id: int | None = None
    expires_in_days: int | None = Field(default=None, gt=0)


class ApiKeyOut(BaseModel):
    id: int
    name: str
    scopes: list[str]
    dept_id: int | None
    expires_at: dt.datetime | None
    revoked_at: dt.datetime | None
    created_by: str | None

    model_config = {"from_attributes": True}


class ApiKeyIssued(ApiKeyOut):
    """Issuance response only — carries the one-time raw key."""

    raw_key: str


@router.post("", status_code=201)
async def issue_api_key(
    body: ApiKeyIn,
    user: CurrentUser = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ApiKeyIssued:
    raw_key = generate_key()
    expires_at = (
        dt.datetime.now(dt.UTC) + dt.timedelta(days=body.expires_in_days)
        if body.expires_in_days
        else None
    )
    row = ApiKey(
        name=body.name,
        hash=hash_key(raw_key),
        scopes=body.scopes,
        dept_id=body.dept_id,
        expires_at=expires_at,
        created_by=user.sub,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return ApiKeyIssued(raw_key=raw_key, **ApiKeyOut.model_validate(row).model_dump())


@router.get("")
async def list_api_keys(
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[ApiKeyOut]:
    rows = (await session.execute(select(ApiKey).order_by(ApiKey.id))).scalars().all()
    return [ApiKeyOut.model_validate(r) for r in rows]


@router.post("/{key_id}/revoke", status_code=204)
async def revoke_api_key(
    key_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    row = await session.get(ApiKey, key_id)
    if row is None:
        raise HTTPException(status_code=404, detail="api key not found")
    if row.revoked_at is None:
        row.revoked_at = dt.datetime.now(dt.UTC)
        await session.commit()

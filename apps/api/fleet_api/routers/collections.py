"""Collections API (task 3.2, TRD §8/§11).

A collection carries the sensitivity/retention/pii_policy that governs every
document uploaded into it (§8: uploads inherit collection sensitivity).
Creating/editing a collection is a MANAGE_DEPT action (dept_admin+, §7.1) —
it sets the governance policy other users' uploads are bound by; browsing is
open to anyone who can UPLOAD.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.db import get_session
from fleet_api.models import Collection
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/collections", tags=["collections"])

_VALID_SENSITIVITY = {"public", "internal", "confidential", "pii"}
_VALID_PII_POLICY = {"redact", "block", "allow-local-only"}


class CollectionIn(BaseModel):
    name: str
    dept_id: int | None = None
    sensitivity: str = "internal"
    retention_days: int | None = Field(default=None, gt=0)
    pii_policy: str = "redact"


class CollectionOut(BaseModel):
    id: int
    name: str
    dept_id: int | None
    sensitivity: str
    retention_days: int | None
    pii_policy: str

    model_config = {"from_attributes": True}


def _validate(body: CollectionIn) -> None:
    if body.sensitivity not in _VALID_SENSITIVITY:
        raise HTTPException(
            status_code=422, detail=f"unknown sensitivity: {body.sensitivity}"
        )
    if body.pii_policy not in _VALID_PII_POLICY:
        raise HTTPException(status_code=422, detail=f"unknown pii_policy: {body.pii_policy}")
    # §8: pii-sensitivity content must never be routed to a policy that could
    # leave it eligible for cloud routing (redact downgrades to internal).
    if body.sensitivity == "pii" and body.pii_policy == "redact":
        raise HTTPException(
            status_code=422,
            detail=(
                "pii collections must use pii_policy 'block' or 'allow-local-only', "
                "not 'redact'"
            ),
        )


@router.post("", status_code=201)
async def create_collection(
    body: CollectionIn,
    _: object = Depends(require_permission(Permission.MANAGE_DEPT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CollectionOut:
    _validate(body)
    existing = (
        await session.execute(select(Collection).where(Collection.name == body.name))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="collection name already exists")

    row = Collection(**body.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return CollectionOut.model_validate(row)


@router.get("")
async def list_collections(
    _: object = Depends(require_permission(Permission.UPLOAD)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[CollectionOut]:
    rows = (await session.execute(select(Collection).order_by(Collection.id))).scalars().all()
    return [CollectionOut.model_validate(r) for r in rows]


@router.get("/{collection_id}")
async def get_collection(
    collection_id: int,
    _: object = Depends(require_permission(Permission.UPLOAD)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CollectionOut:
    row = await session.get(Collection, collection_id)
    if row is None:
        raise HTTPException(status_code=404, detail="collection not found")
    return CollectionOut.model_validate(row)


@router.patch("/{collection_id}")
async def update_collection(
    collection_id: int,
    body: CollectionIn,
    _: object = Depends(require_permission(Permission.MANAGE_DEPT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CollectionOut:
    _validate(body)
    row = await session.get(Collection, collection_id)
    if row is None:
        raise HTTPException(status_code=404, detail="collection not found")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return CollectionOut.model_validate(row)


@router.delete("/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_DEPT)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    row = await session.get(Collection, collection_id)
    if row is None:
        raise HTTPException(status_code=404, detail="collection not found")
    await session.delete(row)
    await session.commit()

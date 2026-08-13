"""Budgets admin CRUD (task 7.1b, TRD §5 budget hierarchy).

The budget hierarchy itself (global -> dept -> agent -> user, soft/hard
limits, period spend) was already built and enforced in task 2.4
(`core.llm.budget.DbBudgetChecker`) — this only exposes admin control over
the `budgets` table rows that checker reads. MANAGE_PLATFORM-gated, same tier
as models/API-key/user admin.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.db import get_session
from fleet_api.models import Budget
from fleet_api.rbac import Permission, require_permission
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/admin/budgets", tags=["admin:budgets"])

_VALID_SCOPE_TYPES = {"global", "dept", "agent", "user"}
_VALID_PERIODS = {"daily", "monthly"}


class BudgetIn(BaseModel):
    scope_type: str
    scope_id: str | None = None
    period: str = "monthly"
    limit_usd: float = Field(gt=0)
    soft_pct: int = Field(default=80, ge=0, le=100)


class BudgetOut(BaseModel):
    id: int
    scope_type: str
    scope_id: str | None
    period: str
    limit_usd: float
    soft_pct: int

    model_config = {"from_attributes": True}


def _validate(body: BudgetIn) -> None:
    if body.scope_type not in _VALID_SCOPE_TYPES:
        raise HTTPException(status_code=422, detail=f"unknown scope_type: {body.scope_type}")
    if body.period not in _VALID_PERIODS:
        raise HTTPException(status_code=422, detail=f"unknown period: {body.period}")
    if body.scope_type == "global" and body.scope_id is not None:
        raise HTTPException(status_code=422, detail="global scope must not have a scope_id")
    if body.scope_type != "global" and body.scope_id is None:
        raise HTTPException(
            status_code=422, detail=f"{body.scope_type} scope requires a scope_id"
        )


@router.post("", status_code=201)
async def create_budget(
    body: BudgetIn,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> BudgetOut:
    _validate(body)
    existing = (
        await session.execute(
            select(Budget).where(
                Budget.scope_type == body.scope_type,
                Budget.scope_id == body.scope_id,
                Budget.period == body.period,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="budget already exists for this scope+period")

    row = Budget(**body.model_dump())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return BudgetOut.model_validate(row)


@router.get("")
async def list_budgets(
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[BudgetOut]:
    rows = (await session.execute(select(Budget).order_by(Budget.id))).scalars().all()
    return [BudgetOut.model_validate(r) for r in rows]


@router.patch("/{budget_id}")
async def update_budget(
    budget_id: int,
    body: BudgetIn,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> BudgetOut:
    _validate(body)
    row = await session.get(Budget, budget_id)
    if row is None:
        raise HTTPException(status_code=404, detail="budget not found")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return BudgetOut.model_validate(row)


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    row = await session.get(Budget, budget_id)
    if row is None:
        raise HTTPException(status_code=404, detail="budget not found")
    await session.delete(row)
    await session.commit()

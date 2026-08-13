"""Users/roles/departments admin (task 7.1, TRD §7.1).

Platform-wide user/role management is MANAGE_PLATFORM-gated, the same tier as
models and API-key admin (task 6.5.9) — no dept-scoped self-service in this
pass, matching those routers' pattern (CLAUDE.md: simplest version that
proves the platform pattern).

A role edit here takes effect on the edited user's very next request: roles
live in the `roles` table, and `auth.get_current_user` re-reads it on every
call rather than trusting the JWT's baked-in claims (task 7.1 AC).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fleet_api.db import get_session
from fleet_api.models import Department, Role, User
from fleet_api.rbac import ROLE_PERMISSIONS, Permission, require_permission
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/admin/users", tags=["admin:users"])
departments_router = APIRouter(prefix="/v1/admin/departments", tags=["admin:users"])

_VALID_ROLES = set(ROLE_PERMISSIONS)


class RoleOut(BaseModel):
    id: int
    role: str
    dept_id: int | None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    kc_sub: str
    display_name: str
    status: str
    dept_id: int | None
    roles: list[RoleOut]


class DeptIn(BaseModel):
    dept_id: int | None


class RoleIn(BaseModel):
    role: str
    dept_id: int | None = None


class DepartmentOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


@router.get("")
async def list_users(
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[UserOut]:
    users = (await session.execute(select(User).order_by(User.id))).scalars().all()
    roles = (await session.execute(select(Role))).scalars().all()
    roles_by_user: dict[int, list[Role]] = {}
    for r in roles:
        roles_by_user.setdefault(r.user_id, []).append(r)
    return [
        UserOut(
            id=u.id,
            kc_sub=u.kc_sub,
            display_name=u.display_name,
            status=u.status,
            dept_id=u.dept_id,
            roles=[RoleOut.model_validate(r) for r in roles_by_user.get(u.id, [])],
        )
        for u in users
    ]


@router.patch("/{user_id}")
async def update_user_dept(
    user_id: int,
    body: DeptIn,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    user.dept_id = body.dept_id
    await session.commit()
    roles = (
        await session.execute(select(Role).where(Role.user_id == user.id))
    ).scalars().all()
    return UserOut(
        id=user.id,
        kc_sub=user.kc_sub,
        display_name=user.display_name,
        status=user.status,
        dept_id=user.dept_id,
        roles=[RoleOut.model_validate(r) for r in roles],
    )


@router.post("/{user_id}/roles", status_code=201)
async def add_role(
    user_id: int,
    body: RoleIn,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RoleOut:
    if body.role not in _VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"unknown role: {body.role}")
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    existing = (
        await session.execute(
            select(Role).where(
                Role.user_id == user_id,
                Role.role == body.role,
                Role.dept_id == body.dept_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="role already assigned")
    row = Role(user_id=user_id, role=body.role, dept_id=body.dept_id)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return RoleOut.model_validate(row)


@router.delete("/{user_id}/roles/{role_id}", status_code=204)
async def remove_role(
    user_id: int,
    role_id: int,
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    row = await session.get(Role, role_id)
    if row is None or row.user_id != user_id:
        raise HTTPException(status_code=404, detail="role not found")
    await session.delete(row)
    await session.commit()


@departments_router.get("")
async def list_departments(
    _: object = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[DepartmentOut]:
    rows = (await session.execute(select(Department).order_by(Department.id))).scalars().all()
    return [DepartmentOut.model_validate(r) for r in rows]

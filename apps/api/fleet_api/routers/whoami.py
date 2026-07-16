"""A protected demo route: returns the caller identity; requires CHAT permission."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fleet_api.auth import CurrentUser
from fleet_api.rbac import Permission, require_permission

router = APIRouter(tags=["whoami"])


@router.get("/whoami")
async def whoami(
    user: CurrentUser = Depends(require_permission(Permission.CHAT)),  # noqa: B008
) -> dict[str, object]:
    return {"sub": user.sub, "roles": sorted(user.roles)}


@router.get("/admin-only")
async def admin_only(
    user: CurrentUser = Depends(require_permission(Permission.MANAGE_PLATFORM)),  # noqa: B008
) -> dict[str, str]:
    return {"ok": "admin"}

"""Role-based access control: roles, permissions, and the enforcement dependency."""

from __future__ import annotations

from enum import StrEnum

from fastapi import Depends
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import ForbiddenError


class Permission(StrEnum):
    CHAT = "chat"
    UPLOAD = "upload"
    MANAGE_AGENTS = "manage_agents"
    APPROVE = "approve"
    MANAGE_DEPT = "manage_dept"
    MANAGE_PLATFORM = "manage_platform"


# TRD §7.1 RBAC matrix. Roles: platform_admin, dept_admin, builder, approver, member.
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "member": {Permission.CHAT, Permission.UPLOAD},
    "builder": {Permission.CHAT, Permission.UPLOAD, Permission.MANAGE_AGENTS},
    "approver": {Permission.CHAT, Permission.UPLOAD, Permission.APPROVE},
    "dept_admin": {
        Permission.CHAT,
        Permission.UPLOAD,
        Permission.MANAGE_AGENTS,
        Permission.APPROVE,
        Permission.MANAGE_DEPT,
    },
    "platform_admin": set(Permission),
}


def permissions_for(roles: set[str]) -> set[Permission]:
    """Union of permissions granted by the user's roles."""
    granted: set[Permission] = set()
    for role in roles:
        granted |= ROLE_PERMISSIONS.get(role, set())
    return granted


def require_permission(perm: Permission):
    """Dependency factory: allow the request only if the user holds `perm`."""

    async def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:  # noqa: B008
        if perm not in permissions_for(user.roles):
            raise ForbiddenError(f"missing permission: {perm}")
        return user

    return _dep

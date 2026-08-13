"""JIT user provisioning and DB-backed role bootstrap/lookup (task 7.1).

Keycloak stays the identity provider (authentication); the `roles` table is
the sole source of truth for authorization from first login onward, so an
admin's role edit is visible on the caller's very next request instead of
waiting on token refresh.
"""

from __future__ import annotations

from fleet_api.models import Role, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_or_create_user(
    session: AsyncSession, *, kc_sub: str, display_name: str | None = None
) -> User:
    """First-login provisioning: a verified Keycloak principal always gets an
    internal users row, rather than requiring every user to be pre-seeded."""
    row = (await session.execute(select(User).where(User.kc_sub == kc_sub))).scalar_one_or_none()
    if row is not None:
        return row
    row = User(kc_sub=kc_sub, email_hash="", display_name=display_name or kc_sub)
    session.add(row)
    await session.flush()
    return row


async def seed_roles_from_jwt(session: AsyncSession, user: User, jwt_roles: set[str]) -> None:
    """Copy the JWT's realm roles into the `roles` table, but only on a
    user's first login (no DB role rows yet). Once any role row exists —
    including rows created here — this is a no-op, so a later admin edit is
    never silently overwritten by whatever Keycloak still says on the token.
    """
    existing = (
        await session.execute(select(Role.id).where(Role.user_id == user.id).limit(1))
    ).first()
    if existing is not None:
        return
    for role in jwt_roles:
        session.add(Role(user_id=user.id, role=role, dept_id=None))
    await session.flush()


async def load_roles(session: AsyncSession, user: User) -> set[str]:
    rows = (await session.execute(select(Role.role).where(Role.user_id == user.id))).scalars().all()
    return set(rows)

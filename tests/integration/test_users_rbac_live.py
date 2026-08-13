"""Integration: JIT user provisioning + DB-backed role bootstrap (task 7.1).

Proves the mechanism behind 7.1's AC ("role change takes effect on next
request"): roles live in the `roles` table, not baked into the JWT. First
login copies the token's realm roles into the DB once; every subsequent
permission check re-reads the DB, so an admin edit is visible on the very
next call with no token refresh or caching involved.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import pytest
from fleet_api.db import get_engine, session_factory
from fleet_api.models import Role, User
from fleet_api.rbac import Permission, permissions_for
from fleet_api.users import get_or_create_user, load_roles, seed_roles_from_jwt
from sqlalchemy import select
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def migrated_pg() -> str:
    with PostgresContainer("postgres:16") as pg:
        raw = pg.get_connection_url()
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        os.environ["FLEET_DATABASE_URL"] = raw.replace("+psycopg2", "+asyncpg")
        yield os.environ["FLEET_DATABASE_URL"]


def test_get_or_create_user_is_idempotent_by_kc_sub(migrated_pg: str) -> None:
    async def _run() -> None:
        engine = get_engine(migrated_pg)
        session = session_factory(engine)()
        try:
            first = await get_or_create_user(session, kc_sub="sub-idempotent")
            await session.commit()
            second = await get_or_create_user(session, kc_sub="sub-idempotent")
            assert second.id == first.id

            rows = (
                await session.execute(select(User).where(User.kc_sub == "sub-idempotent"))
            ).scalars().all()
            assert len(rows) == 1
        finally:
            await session.close()
            await engine.dispose()

    asyncio.run(_run())


def test_seed_roles_from_jwt_bootstraps_once_then_never_overwrites(migrated_pg: str) -> None:
    async def _run() -> None:
        engine = get_engine(migrated_pg)
        session = session_factory(engine)()
        try:
            user = await get_or_create_user(session, kc_sub="sub-bootstrap")
            await session.commit()

            # First login: DB has no roles yet, so the JWT's roles seed it.
            await seed_roles_from_jwt(session, user, {"member"})
            await session.commit()
            assert await load_roles(session, user) == {"member"}

            # Second login with a *different* JWT role set must not touch the
            # DB rows an admin may have since edited by hand.
            await seed_roles_from_jwt(session, user, {"builder"})
            await session.commit()
            assert await load_roles(session, user) == {"member"}
        finally:
            await session.close()
            await engine.dispose()

    asyncio.run(_run())


def test_admin_role_edit_is_visible_on_next_load(migrated_pg: str) -> None:
    """The literal 7.1 AC: an admin edit to the roles table changes what
    permissions_for() grants on the very next read, no refresh needed."""

    async def _run() -> None:
        engine = get_engine(migrated_pg)
        session = session_factory(engine)()
        try:
            user = await get_or_create_user(session, kc_sub="sub-promote")
            await session.commit()
            await seed_roles_from_jwt(session, user, {"member"})
            await session.commit()

            roles_before = await load_roles(session, user)
            assert permissions_for(roles_before) == {Permission.CHAT, Permission.UPLOAD}

            # Simulate the admin endpoint granting platform_admin.
            session.add(Role(user_id=user.id, role="platform_admin", dept_id=None))
            await session.commit()

            roles_after = await load_roles(session, user)
            assert permissions_for(roles_after) == set(Permission)
        finally:
            await session.close()
            await engine.dispose()

    asyncio.run(_run())

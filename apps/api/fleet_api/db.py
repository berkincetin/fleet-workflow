"""Async database engine, session factory, and URL resolution for the Fleet API."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"


def database_url() -> str:
    """Return the async database URL from FLEET_DATABASE_URL, or the local default."""
    return os.environ.get("FLEET_DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine(url: str | None = None) -> AsyncEngine:
    """Create an async engine for the given URL (defaults to database_url())."""
    return create_async_engine(url or database_url(), pool_pre_ping=True)


def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the given engine."""
    return async_sessionmaker(engine, expire_on_commit=False)

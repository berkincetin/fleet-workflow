"""Async database engine, session factory, and URL resolution for the Fleet API."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from functools import lru_cache

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


@lru_cache(maxsize=1)
def _app_session_factory() -> async_sessionmaker[AsyncSession]:
    """Process-wide session factory over a single engine (built lazily)."""
    return session_factory(get_engine())


def reset_engine_cache() -> None:
    """Drop the cached engine/session factory so the next `get_session()`
    call builds a fresh one bound to the current event loop.

    Only needed in test suites that create multiple event loops within one
    process (e.g. instantiating `TestClient(create_app())` more than once
    per module) — a real server process has exactly one loop for its
    lifetime, so this is never called in production."""
    _app_session_factory.cache_clear()


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped async session."""
    async with _app_session_factory()() as session:
        yield session

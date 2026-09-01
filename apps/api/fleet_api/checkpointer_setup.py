"""Create LangGraph's Postgres checkpointer tables (`checkpoints`,
`checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`).

These are owned by `AsyncPostgresSaver`, not by Alembic, so `alembic upgrade
head` alone leaves a fresh database without them and every HITL agent run
(dev/invoice/hr) fails at its first checkpoint write with
`UndefinedTable: relation "checkpoints" does not exist`. Until task 8.5 the
only thing that ever called `.setup()` was a single integration test, so a
fresh stack happened to work only if that test had been run first — which is
exactly how this bit after a Docker Desktop restart wiped the volumes.

Wired into `make migrate` so schema setup is one step. `.setup()` is
idempotent (it keeps its own `checkpoint_migrations` ledger), so re-running is
safe and cheap.
"""

from __future__ import annotations

import asyncio
import sys

from fleet_api.db import database_url


async def _setup() -> None:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    # langgraph's saver takes a psycopg (not asyncpg) DSN.
    dsn = database_url().replace("postgresql+asyncpg://", "postgresql://")
    async with AsyncPostgresSaver.from_conn_string(dsn) as checkpointer:
        await checkpointer.setup()


def main() -> None:
    if sys.platform == "win32":
        # psycopg's async path can't run on Windows' default ProactorEventLoop.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(_setup())
    print("langgraph checkpointer tables ready")


if __name__ == "__main__":
    main()

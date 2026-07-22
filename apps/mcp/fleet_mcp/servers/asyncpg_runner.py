"""Real QueryRunner for pg_ro.PgReadOnlyTool, over the `fleet_readonly` role
(task 5.1). Connects with asyncpg directly (not the SQLAlchemy ORM engine
apps/api uses) since this only ever runs bounded, pre-validated read SQL.

`fleet_readonly` is NOLOGIN (migration 0001, CLAUDE.md rule 7 — it must stay
read-only, not become a second set of login credentials to manage). Instead
this connects as the normal app user and issues `SET ROLE fleet_readonly` on
the connection before running the query, so even if PgReadOnlyTool's own
checks were somehow bypassed, the DB session itself only has SELECT granted
(migration 0007 grants `fleet` membership in `fleet_readonly` so the switch
is permitted).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import asyncpg


@dataclass
class AsyncpgRunner:
    dsn: str

    async def run(
        self, sql: str, *, timeout: float  # noqa: ASYNC109 — passed straight to asyncpg's own timeout
    ) -> list[dict[str, Any]]:
        conn = await asyncpg.connect(self.dsn)
        try:
            await conn.execute("SET ROLE fleet_readonly")
            records = await conn.fetch(sql, timeout=timeout)
            return [dict(r) for r in records]
        finally:
            await conn.close()


def build_default_runner() -> AsyncpgRunner:
    dsn = os.environ.get(
        "FLEET_DATABASE_DSN",
        "postgresql://fleet:fleet_dev_pw@localhost:5432/fleet",
    )
    return AsyncpgRunner(dsn=dsn)

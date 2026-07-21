"""Spend-ledger sink (task 2.3, TRD §5).

Appends one row per LLM call to ``spend_ledger`` (tokens in/out/cached, computed
cost, agent/user/dept, trace_id). The client computes the row; this sink only
persists it. Table-name/column contract matches migration 0003.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker


class SpendLedger:
    """Async writer for spend_ledger rows over a SQLAlchemy session factory."""

    _INSERT = text(
        "INSERT INTO spend_ledger "
        "(model, agent_id, user_id, dept_id, tok_in, tok_out, tok_cached, cost_usd, trace_id) "
        "VALUES (:model, :agent_id, :user_id, :dept_id, :tok_in, :tok_out, "
        ":tok_cached, :cost_usd, :trace_id)"
    )

    def __init__(self, session_factory: async_sessionmaker[Any]) -> None:
        self._session_factory = session_factory

    async def record(self, row: dict[str, Any]) -> None:
        async with self._session_factory() as session:
            await session.execute(
                self._INSERT,
                {
                    "model": row["model"],
                    "agent_id": row.get("agent_id"),
                    "user_id": row.get("user_id"),
                    "dept_id": row.get("dept_id"),
                    "tok_in": row.get("tok_in", 0),
                    "tok_out": row.get("tok_out", 0),
                    "tok_cached": row.get("tok_cached", 0),
                    "cost_usd": row.get("cost_usd", 0.0),
                    "trace_id": row.get("trace_id"),
                },
            )
            await session.commit()

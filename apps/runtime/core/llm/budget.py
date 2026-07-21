"""Budget pre-check (task 2.4, TRD §5).

Pure decision (``evaluate_budget``) plus an async pre-check (``check_budget``)
that aggregates a scope's spend over the current period from ``spend_ledger`` and
evaluates it against the scope's ``budgets`` row. Hierarchy: global → dept →
agent → user; a hard stop at any level blocks the call (§5). The soft-limit flag
is surfaced in LLM response metadata; the hard stop raises ``BudgetExceeded`` (a
402-style domain error, §4.4).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker


class BudgetExceeded(Exception):
    """Raised when a scope has reached/exceeded its hard (100%) budget limit."""

    def __init__(self, scope: str, spent_usd: float, limit_usd: float) -> None:
        self.scope = scope
        self.spent_usd = spent_usd
        self.limit_usd = limit_usd
        super().__init__(
            f"budget exceeded for {scope}: spent ${spent_usd:.2f} of ${limit_usd:.2f}"
        )


@dataclass(frozen=True)
class BudgetStatus:
    """Outcome of evaluating spend against a budget for one scope."""

    scope: str
    spent_usd: float
    limit_usd: float | None
    soft_pct: int
    allowed: bool
    soft_exceeded: bool
    hard_exceeded: bool
    utilization: float

    def raise_if_exceeded(self, *, scope: str | None = None) -> None:
        if self.hard_exceeded:
            raise BudgetExceeded(
                scope or self.scope, self.spent_usd, self.limit_usd or 0.0
            )


def evaluate_budget(
    *,
    spent_usd: float,
    limit_usd: float | None,
    soft_pct: int,
    scope: str = "",
) -> BudgetStatus:
    """Decide allow/soft/hard for `spent_usd` against `limit_usd`.

    No limit (``None``) → unlimited: allowed, never flagged. Otherwise soft is
    reached at ``soft_pct`` of the limit, hard at 100%.
    """
    if limit_usd is None:
        return BudgetStatus(
            scope=scope,
            spent_usd=spent_usd,
            limit_usd=None,
            soft_pct=soft_pct,
            allowed=True,
            soft_exceeded=False,
            hard_exceeded=False,
            utilization=0.0,
        )

    utilization = spent_usd / limit_usd if limit_usd > 0 else 1.0
    hard = spent_usd >= limit_usd
    soft = spent_usd >= limit_usd * (soft_pct / 100.0)
    return BudgetStatus(
        scope=scope,
        spent_usd=spent_usd,
        limit_usd=limit_usd,
        soft_pct=soft_pct,
        allowed=not hard,
        soft_exceeded=soft,
        hard_exceeded=hard,
        utilization=utilization,
    )


def _period_start(period: str, now: dt.datetime) -> dt.datetime:
    """Start of the current budget period (only 'monthly' and 'daily' for now)."""
    if period == "daily":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    # default monthly
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class DbBudgetChecker:
    """Client budget checker over the DB: evaluates every scope present on the
    call meta (global → dept → agent → user) and returns the most-constrained
    status. A hard stop at any level blocks the call (§5 hierarchy)."""

    def __init__(self, session_factory: async_sessionmaker[Any]) -> None:
        self._session_factory = session_factory

    async def __call__(self, meta: dict[str, Any]) -> BudgetStatus:
        scopes: list[tuple[str, str | None]] = [("global", None)]
        if meta.get("dept_id"):
            scopes.append(("dept", str(meta["dept_id"])))
        if meta.get("agent_id"):
            scopes.append(("agent", str(meta["agent_id"])))
        if meta.get("user_id"):
            scopes.append(("user", str(meta["user_id"])))

        statuses = [
            await check_budget(self._session_factory, scope_type=st, scope_id=sid)
            for st, sid in scopes
        ]
        # Any hard stop wins; else any soft flag; else the highest-utilization one.
        for s in statuses:
            if s.hard_exceeded:
                return s
        soft = [s for s in statuses if s.soft_exceeded]
        if soft:
            return max(soft, key=lambda s: s.utilization)
        return max(statuses, key=lambda s: s.utilization)


async def check_budget(
    session_factory: async_sessionmaker[Any],
    *,
    scope_type: str,
    scope_id: str | None,
    now: dt.datetime | None = None,
) -> BudgetStatus:
    """Load the scope's budget + period spend and evaluate. Missing budget row →
    unlimited (allowed)."""
    now = now or dt.datetime.now(dt.UTC)
    label = f"{scope_type}:{scope_id}" if scope_id else scope_type

    async with session_factory() as session:
        budget = (
            await session.execute(
                text(
                    "SELECT limit_usd, soft_pct, period FROM budgets "
                    "WHERE scope_type = :st AND "
                    "(scope_id = :sid OR (scope_id IS NULL AND :sid IS NULL)) "
                    "LIMIT 1"
                ),
                {"st": scope_type, "sid": scope_id},
            )
        ).first()

        if budget is None:
            return evaluate_budget(
                spent_usd=0.0, limit_usd=None, soft_pct=80, scope=label
            )

        limit_usd, soft_pct, period = budget
        start = _period_start(period, now)

        # Literal per-scope queries (no interpolated identifiers, even from a
        # trusted lookup) so no SQL string is ever built from a variable part.
        if scope_type == "global":
            spend_sql = "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger WHERE ts >= :start"
            params: dict[str, Any] = {"start": start}
        elif scope_type == "dept":
            spend_sql = (
                "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger "
                "WHERE ts >= :start AND dept_id = :sid"
            )
            params = {"start": start, "sid": scope_id}
        elif scope_type == "agent":
            spend_sql = (
                "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger "
                "WHERE ts >= :start AND agent_id = :sid"
            )
            params = {"start": start, "sid": scope_id}
        elif scope_type == "user":
            spend_sql = (
                "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger "
                "WHERE ts >= :start AND user_id = :sid"
            )
            params = {"start": start, "sid": scope_id}
        else:
            raise ValueError(f"unknown scope_type: {scope_type}")

        spent = (await session.execute(text(spend_sql), params)).scalar_one()

    return evaluate_budget(
        spent_usd=float(spent),
        limit_usd=float(limit_usd),
        soft_pct=int(soft_pct),
        scope=label,
    )

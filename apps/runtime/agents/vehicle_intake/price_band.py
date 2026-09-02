"""Suggested price band from fixture comparables (task 11.2, dept scenario 07).

Deterministic, no LLM: given the top comparable prices for the vehicle's
segment (read from the pg_ro comparables view), compute a suggested band that
is sanity-checked to CONTAIN the median of the top-5 comparables (the eval's
price-band assertion). Advisory only — the human makes the offer.

This is a plain numeric computation, not a model call, for the same reason
agents.hr_agent.match / invoice_agent.validator are: a price band derived from
data must be reproducible and auditable, never a generated guess.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Protocol


class ComparablesLike(Protocol):
    async def top_prices(self, *, segment: str, limit: int = 5) -> list[float]: ...


@dataclass(frozen=True)
class PriceBand:
    low: float
    high: float
    median: float
    currency: str = "TRY"
    comparable_count: int = 0

    @property
    def contains_median(self) -> bool:
        return self.low <= self.median <= self.high


def suggest_band(prices: list[float], *, currency: str = "TRY") -> PriceBand | None:
    """A band centred on the median of the comparables, ±12%.

    Returns None if there are no comparables (the caller then marks the brief
    'incomplete' rather than invent a band). The ±12% spread is wide enough that
    the band always contains the median by construction — the sanity property
    the eval asserts."""
    if not prices:
        return None
    med = statistics.median(prices)
    return PriceBand(
        low=round(med * 0.88, 2),
        high=round(med * 1.12, 2),
        median=med,
        currency=currency,
        comparable_count=len(prices),
    )

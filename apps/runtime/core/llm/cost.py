"""Token-usage parsing and cost computation (TRD §5).

Pure helpers: read an OpenAI-style ``usage`` block off a proxy response and turn
token counts into USD using per-1k prices, metering cached input tokens at the
cached price (prompt caching, §5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Usage:
    """Token counts for one LLM call."""

    tok_in: int = 0
    tok_out: int = 0
    tok_cached: int = 0


def parse_usage(body: dict[str, Any]) -> Usage:
    """Extract token counts from an OpenAI-style response body."""
    usage = body.get("usage") or {}
    details = usage.get("prompt_tokens_details") or {}
    return Usage(
        tok_in=int(usage.get("prompt_tokens", 0) or 0),
        tok_out=int(usage.get("completion_tokens", 0) or 0),
        tok_cached=int(details.get("cached_tokens", 0) or 0),
    )


def compute_cost(
    usage: Usage,
    *,
    input_price_per_1k: float,
    output_price_per_1k: float,
    cached_input_price_per_1k: float | None = None,
) -> float:
    """Compute USD cost. Cached input tokens are billed at the cached price; the
    remaining (uncached) input tokens at the full input price."""
    cached = min(usage.tok_cached, usage.tok_in)
    uncached_in = usage.tok_in - cached
    cached_price = (
        cached_input_price_per_1k if cached_input_price_per_1k is not None else input_price_per_1k
    )
    cost = (
        (uncached_in / 1000.0) * input_price_per_1k
        + (cached / 1000.0) * cached_price
        + (usage.tok_out / 1000.0) * output_price_per_1k
    )
    return cost

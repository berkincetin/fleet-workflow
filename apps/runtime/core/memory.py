"""Conversation context budgeting: rolling window + summarized eviction (TRD §5).

Keeps the most recent ``max_turns`` messages verbatim; anything older is folded
into a running summary via the utility model (§4.3: summarization is a utility
call-site, not reasoning) rather than dropped, so long conversations stay
grounded in what was already discussed without unbounded context growth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

_SUMMARY_PROMPT = (
    "Summarize the following conversation turns in 2-4 sentences, preserving "
    "any facts, decisions, or open questions a later reply might need."
)


class SummaryClient(Protocol):
    async def utility(self, messages: list[dict[str, Any]], **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class Context:
    """The context to feed a call: an optional rolling summary plus recent turns."""

    summary: str | None
    recent: list[dict[str, Any]]


async def build_context(
    history: list[dict[str, Any]],
    *,
    max_turns: int,
    summary_client: SummaryClient,
) -> Context:
    """Split history into (summary of evicted turns, recent verbatim turns)."""
    if len(history) <= max_turns:
        return Context(summary=None, recent=list(history))

    evicted, recent = history[:-max_turns], history[-max_turns:]
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in evicted)
    response = await summary_client.utility(
        [
            {"role": "system", "content": _SUMMARY_PROMPT},
            {"role": "user", "content": transcript},
        ]
    )
    return Context(summary=response.content, recent=recent)

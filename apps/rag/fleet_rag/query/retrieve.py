"""Hybrid retrieval + context budgeting (task 3.3, TRD §5).

Dense kNN search over Qdrant, optionally narrowed by a keyword (full-text)
filter on the chunk content. Two context budgets from §5 are enforced here
rather than left to the caller: a per-chunk token cap (truncate any
over-long chunk) and a total retrieved-tokens cap (drop the lowest-scoring
chunks once the budget is spent — results arrive score-sorted from Qdrant).
The Qdrant call itself is injected as `searcher` so this stays pure/testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Hit:
    id: str
    score: float
    document_id: int
    # content_sha256 — the chunks table's natural key, known at retrieval time
    # (the DB-assigned chunks.id isn't in the Qdrant payload; see pipeline.py).
    chunk_ref: str
    content: str
    redacted: bool


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = 5
    per_chunk_token_cap: int = 500
    total_token_cap: int = 4000


class Searcher(Protocol):
    def __call__(
        self, *, query_vector: list[float], top_k: int, keyword: str | None = None
    ) -> list[Hit]: ...


def _truncate(hit: Hit, *, max_tokens: int) -> Hit:
    words = hit.content.split()
    if len(words) <= max_tokens:
        return hit
    return Hit(
        id=hit.id,
        score=hit.score,
        document_id=hit.document_id,
        chunk_ref=hit.chunk_ref,
        content=" ".join(words[:max_tokens]),
        redacted=hit.redacted,
    )


async def retrieve(
    searcher: Searcher,
    *,
    query_vector: list[float],
    config: RetrievalConfig,
    keyword: str | None = None,
) -> list[Hit]:
    raw_hits = searcher(query_vector=query_vector, top_k=config.top_k, keyword=keyword)
    capped = [_truncate(h, max_tokens=config.per_chunk_token_cap) for h in raw_hits]

    kept: list[Hit] = []
    spent = 0
    for hit in capped:  # already score-sorted (best first) by the searcher/Qdrant
        tokens = len(hit.content.split())
        if spent + tokens > config.total_token_cap and kept:
            break
        kept.append(hit)
        spent += tokens
    return kept

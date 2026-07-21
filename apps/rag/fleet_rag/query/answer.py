"""Grounded answer + citation guardrail (task 3.3, TRD §9 structural check).

Every RAG answer must carry >=1 citation, and every citation must resolve to
a chunk actually retrieved that run. A `generate` call producing an
ungrounded answer (no citations, or a citation to a position outside the
retrieved set) is retried once; a second failure degrades to a fixed
"I don't know" response rather than surface an unverifiable claim.

Citations are 1-indexed positions into the retrieved `hits` list (the
generator is prompted with `[chunk:1]`, `[chunk:2]`, ... for the N hits it
was given) — resolving through the *position* rather than the underlying
chunk_ref keeps the LLM's citation markers short regardless of what the
chunk's real identifier looks like.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fleet_rag.query.retrieve import Hit

DEGRADED_ANSWER = (
    "I don't know based on the available documents. This has been flagged for follow-up."
)


@dataclass(frozen=True)
class Citation:
    chunk_ref: str
    document_id: int


@dataclass(frozen=True)
class Answer:
    text: str
    citations: list[Citation]
    degraded: bool = False


class Generator(Protocol):
    async def __call__(
        self, *, question: str, hits: list[Hit]
    ) -> tuple[str, list[int]]: ...


def _resolve_citations(positions: list[int], hits: list[Hit]) -> list[Citation] | None:
    """Return citations if every 1-indexed position resolves to a retrieved hit."""
    if not positions:
        return None
    citations: list[Citation] = []
    for position in positions:
        if position < 1 or position > len(hits):
            return None
        hit = hits[position - 1]
        citations.append(Citation(chunk_ref=hit.chunk_ref, document_id=hit.document_id))
    return citations


async def build_answer(
    *, question: str, hits: list[Hit], generate: Generator, max_attempts: int = 2
) -> Answer:
    if not hits:
        return Answer(text=DEGRADED_ANSWER, citations=[], degraded=True)

    for _attempt in range(max_attempts):
        text, chunk_ids = await generate(question=question, hits=hits)
        citations = _resolve_citations(chunk_ids, hits)
        if citations is not None:
            return Answer(text=text, citations=citations, degraded=False)

    return Answer(text=DEGRADED_ANSWER, citations=[], degraded=True)

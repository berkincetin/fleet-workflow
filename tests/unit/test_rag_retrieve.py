"""Hybrid retrieval + context budgeting (task 3.3, TRD §5).

Dense search plus an optional keyword filter, with per-agent top_k, a
per-chunk token cap (truncate any over-long chunk), and a total
retrieved-tokens cap (drop lowest-scoring chunks once the budget is spent).
The actual Qdrant call is injected (a plain callable) so this stays a pure
unit test; the live wiring is qdrant_store.search plus a text-index filter,
covered in the live integration test.
"""

from __future__ import annotations

from fleet_rag.query.retrieve import Hit, RetrievalConfig, retrieve


def _hit(id_: str, score: float, content: str, document_id: int = 1) -> Hit:
    return Hit(
        id=id_,
        score=score,
        document_id=document_id,
        chunk_ref=f"sha-{id_}",
        content=content,
        redacted=False,
    )


class _FakeSearcher:
    def __init__(self, hits: list[Hit]) -> None:
        self.hits = hits
        self.calls: list[dict] = []

    def __call__(self, *, query_vector, top_k, keyword=None):  # type: ignore[no-untyped-def]
        self.calls.append({"query_vector": query_vector, "top_k": top_k, "keyword": keyword})
        return self.hits[:top_k]


async def test_retrieve_respects_top_k() -> None:
    hits = [_hit(f"c-{i}", score=1.0 - i * 0.1, content=f"chunk {i}") for i in range(10)]
    searcher = _FakeSearcher(hits)
    result = await retrieve(
        searcher, query_vector=[0.1], config=RetrievalConfig(top_k=3)
    )
    assert len(result) == 3
    assert searcher.calls[0]["top_k"] == 3


async def test_retrieve_truncates_chunk_over_per_chunk_token_cap() -> None:
    long_content = "word " * 500
    hits = [_hit("c-1", score=0.9, content=long_content)]
    searcher = _FakeSearcher(hits)
    result = await retrieve(
        searcher, query_vector=[0.1], config=RetrievalConfig(top_k=5, per_chunk_token_cap=50)
    )
    assert len(result[0].content.split()) <= 50


async def test_retrieve_drops_lowest_scoring_once_total_token_budget_spent() -> None:
    # Each chunk ~100 words; total cap 250 -> only 2 fit, kept by score order.
    hits = [
        _hit("c-1", score=0.95, content="alpha " * 100),
        _hit("c-2", score=0.9, content="beta " * 100),
        _hit("c-3", score=0.5, content="gamma " * 100),
    ]
    searcher = _FakeSearcher(hits)
    result = await retrieve(
        searcher, query_vector=[0.1], config=RetrievalConfig(top_k=5, total_token_cap=250)
    )
    assert [h.id for h in result] == ["c-1", "c-2"]


async def test_retrieve_passes_keyword_through_to_searcher() -> None:
    searcher = _FakeSearcher([_hit("c-1", 0.9, "content")])
    await retrieve(
        searcher, query_vector=[0.1], config=RetrievalConfig(top_k=5), keyword="invoice"
    )
    assert searcher.calls[0]["keyword"] == "invoice"

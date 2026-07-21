"""RAG query orchestration (task 3.3): embed -> retrieve -> generate -> cite.

All external calls (embeddings, searcher, reasoning) are faked so this stays
a pure unit test of the wiring; the live LLM+Qdrant path is covered in
tests/integration/test_rag_query_live.py.
"""

from __future__ import annotations

from fleet_rag.query.retrieve import Hit
from fleet_rag.query.service import AgentQueryConfig, answer_query


class _FakeEmbedResponse:
    def __init__(self, vector: list[float]) -> None:
        self.vectors = [vector]


class _FakeEmbedClient:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector
        self.calls: list[list[str]] = []

    async def embeddings(self, texts, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(texts)
        return _FakeEmbedResponse(self._vector)


class _FakeReasoningResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeReasoningClient:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[dict] = []

    async def reasoning(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append({"messages": messages, **kwargs})
        return _FakeReasoningResponse(self._content)


def _searcher(hits: list[Hit]):  # type: ignore[no-untyped-def]
    def _search(*, query_vector, top_k, keyword=None):  # type: ignore[no-untyped-def]
        return hits[:top_k]

    return _search


async def test_answer_query_returns_grounded_answer_with_citation() -> None:
    hits = [
        Hit(id="p1", score=0.9, document_id=1, chunk_ref="sha-1",
            content="Fleet was founded in 2024.", redacted=False),
    ]
    embed = _FakeEmbedClient([0.1, 0.2])
    reasoning = _FakeReasoningClient("Fleet was founded in 2024. [chunk:1]")
    answer = await answer_query(
        question="When was Fleet founded?",
        searcher=_searcher(hits),
        embed_client=embed,
        reasoning_client=reasoning,
        config=AgentQueryConfig(),
    )
    assert answer.degraded is False
    assert answer.citations[0].chunk_ref == "sha-1"
    assert embed.calls == [["When was Fleet founded?"]]


async def test_answer_query_degrades_when_no_hits_retrieved() -> None:
    embed = _FakeEmbedClient([0.1, 0.2])
    reasoning = _FakeReasoningClient("should never be called")
    answer = await answer_query(
        question="anything?",
        searcher=_searcher([]),
        embed_client=embed,
        reasoning_client=reasoning,
        config=AgentQueryConfig(),
    )
    assert answer.degraded is True
    assert reasoning.calls == []


async def test_answer_query_passes_sensitivity_through_to_both_calls() -> None:
    hits = [
        Hit(id="p1", score=0.9, document_id=1, chunk_ref="sha-1", content="secret",
            redacted=False)
    ]
    embed = _FakeEmbedClient([0.1])
    reasoning = _FakeReasoningClient("secret info [chunk:1]")
    await answer_query(
        question="q",
        searcher=_searcher(hits),
        embed_client=embed,
        reasoning_client=reasoning,
        config=AgentQueryConfig(),
        sensitivity="pii",
    )
    assert reasoning.calls[0]["sensitivity"] == "pii"


async def test_answer_query_respects_agent_top_k() -> None:
    hits = [
        Hit(id=f"p{i}", score=1.0 - i * 0.1, document_id=1, chunk_ref=f"sha-{i}",
            content=f"chunk {i}", redacted=False)
        for i in range(10)
    ]
    seen_top_k = {}

    def _search(*, query_vector, top_k, keyword=None):  # type: ignore[no-untyped-def]
        seen_top_k["value"] = top_k
        return hits[:top_k]

    embed = _FakeEmbedClient([0.1])
    reasoning = _FakeReasoningClient("answer [chunk:1]")
    await answer_query(
        question="q",
        searcher=_search,
        embed_client=embed,
        reasoning_client=reasoning,
        config=AgentQueryConfig(top_k=2),
    )
    assert seen_top_k["value"] == 2

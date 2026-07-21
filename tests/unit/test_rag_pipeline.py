"""Ingestion pipeline orchestration (task 3.1): extract -> OCR -> PII -> chunk
-> dedup -> embed -> Qdrant upsert. All I/O (LLM client, Qdrant, DB row
lookups) is injected so this runs without Docker; live wiring is exercised in
tests/integration/test_rag_ingest_live.py.
"""

from __future__ import annotations

from fleet_rag.ingest.pipeline import IngestOutcome, run_ingestion


class _FakeEmbeddingResponse:
    def __init__(self, n: int) -> None:
        self.vectors = [[0.1, 0.2, 0.3] for _ in range(n)]
        self.model = "embeddings"


class _FakeLLMClient:
    def __init__(self) -> None:
        self.embed_calls: list[list[str]] = []

    async def embeddings(self, texts, **_kwargs):  # type: ignore[no-untyped-def]
        self.embed_calls.append(texts)
        return _FakeEmbeddingResponse(len(texts))


class _FakeQdrant:
    def __init__(self) -> None:
        self.ensured: list[tuple[str, int]] = []
        self.upserted: list[dict] = []

    def ensure_collection(self, name, *, vector_size):  # type: ignore[no-untyped-def]
        self.ensured.append((name, vector_size))

    def upsert(self, name, *, points):  # type: ignore[no-untyped-def]
        self.upserted.append({"name": name, "points": points})


_TWO_CHUNK_TEXT = ("alpha " * 400 + "\n\n" + "beta " * 400).encode()


async def test_run_ingestion_txt_happy_path() -> None:
    llm = _FakeLLMClient()
    qdrant = _FakeQdrant()
    outcome = await run_ingestion(
        data=_TWO_CHUNK_TEXT,
        filename="notes.txt",
        collection_id=1,
        sensitivity="internal",
        pii_policy="redact",
        llm_client=llm,
        qdrant=qdrant,
        existing_hashes=set(),
    )
    assert isinstance(outcome, IngestOutcome)
    assert outcome.chunks_embedded == 2
    assert outcome.chunks_skipped == 0
    assert len(llm.embed_calls) == 1
    assert len(qdrant.upserted) == 1
    assert qdrant.ensured[0][0] == "fleet_1"


async def test_run_ingestion_skips_chunks_already_embedded() -> None:
    llm = _FakeLLMClient()
    qdrant = _FakeQdrant()
    from fleet_rag.ingest.chunk import chunk_text

    existing = {chunk_text(_TWO_CHUNK_TEXT.decode())[0].content_sha256}

    outcome = await run_ingestion(
        data=_TWO_CHUNK_TEXT,
        filename="notes.txt",
        collection_id=1,
        sensitivity="internal",
        pii_policy="redact",
        llm_client=llm,
        qdrant=qdrant,
        existing_hashes=existing,
    )
    assert outcome.chunks_embedded == 1
    assert outcome.chunks_skipped == 1


async def test_run_ingestion_reupload_with_all_chunks_cached_embeds_nothing() -> None:
    # AC 3.1: re-upload of the same doc costs 0 new embeddings.
    llm = _FakeLLMClient()
    qdrant = _FakeQdrant()
    from fleet_rag.ingest.chunk import chunk_text

    text = "Paragraph one has content.\n\nParagraph two has more content."
    existing = {c.content_sha256 for c in chunk_text(text)}

    outcome = await run_ingestion(
        data=text.encode(),
        filename="notes.txt",
        collection_id=1,
        sensitivity="internal",
        pii_policy="redact",
        llm_client=llm,
        qdrant=qdrant,
        existing_hashes=existing,
    )
    assert outcome.chunks_embedded == 0
    assert llm.embed_calls == []


async def test_run_ingestion_block_policy_drops_chunks_with_pii() -> None:
    llm = _FakeLLMClient()
    qdrant = _FakeQdrant()
    outcome = await run_ingestion(
        data=b"Contact jane@example.com for details.",
        filename="notes.txt",
        collection_id=1,
        sensitivity="internal",
        pii_policy="block",
        llm_client=llm,
        qdrant=qdrant,
        existing_hashes=set(),
    )
    assert outcome.chunks_embedded == 0
    assert outcome.chunks_blocked == 1


async def test_run_ingestion_redact_policy_marks_chunks_redacted() -> None:
    llm = _FakeLLMClient()
    qdrant = _FakeQdrant()
    outcome = await run_ingestion(
        data=b"Contact jane@example.com for details.",
        filename="notes.txt",
        collection_id=1,
        sensitivity="confidential",
        pii_policy="redact",
        llm_client=llm,
        qdrant=qdrant,
        existing_hashes=set(),
    )
    assert outcome.chunks_embedded == 1
    payload = qdrant.upserted[0]["points"][0]["payload"]
    assert payload["redacted"] is True
    assert payload["original_sensitivity"] == "confidential"
    assert "jane@example.com" not in payload["content"]


async def test_run_ingestion_needs_ocr_uses_ocr_fn() -> None:
    llm = _FakeLLMClient()
    qdrant = _FakeQdrant()

    async def _fake_ocr(_data: bytes) -> str:
        return "OCR extracted text from the scan."

    outcome = await run_ingestion(
        data=b"\x89PNG",
        filename="scan.png",
        collection_id=1,
        sensitivity="internal",
        pii_policy="redact",
        llm_client=llm,
        qdrant=qdrant,
        existing_hashes=set(),
        ocr_fn=_fake_ocr,
    )
    assert outcome.chunks_embedded == 1
    assert outcome.used_ocr is True

"""Structure-aware chunking + content-hash dedup (task 3.1).

AC: re-upload of the same doc costs 0 new embeddings — chunk() must produce
stable content hashes so the pipeline can skip already-embedded chunks.
"""

from __future__ import annotations

from fleet_rag.ingest.chunk import Chunk, chunk_text, dedup_chunks


def test_chunk_text_splits_on_paragraph_boundaries() -> None:
    text = "First paragraph.\n\n" + ("word " * 200) + "\n\nLast paragraph."
    chunks = chunk_text(text, max_tokens=50)
    assert len(chunks) > 1
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_text_respects_max_tokens_budget() -> None:
    text = "word " * 1000
    chunks = chunk_text(text, max_tokens=100)
    # A rough token estimate (whitespace split) must stay within budget per chunk.
    assert all(len(c.content.split()) <= 100 for c in chunks)


def test_chunk_text_empty_input_returns_no_chunks() -> None:
    assert chunk_text("", max_tokens=100) == []
    assert chunk_text("   \n\n  ", max_tokens=100) == []


def test_chunk_content_sha256_is_stable_for_identical_content() -> None:
    a = chunk_text("hello world", max_tokens=100)[0]
    b = chunk_text("hello world", max_tokens=100)[0]
    assert a.content_sha256 == b.content_sha256


def test_chunk_content_sha256_differs_for_different_content() -> None:
    a = chunk_text("hello world", max_tokens=100)[0]
    b = chunk_text("goodbye world", max_tokens=100)[0]
    assert a.content_sha256 != b.content_sha256


def test_dedup_chunks_drops_hashes_already_seen() -> None:
    chunks = chunk_text("alpha beta\n\ngamma delta", max_tokens=100)
    existing = {chunks[0].content_sha256}
    fresh = dedup_chunks(chunks, existing_hashes=existing)
    assert chunks[0] not in fresh
    assert len(fresh) == len(chunks) - 1


def test_dedup_chunks_no_existing_hashes_keeps_all() -> None:
    chunks = chunk_text("alpha beta\n\ngamma delta", max_tokens=100)
    assert dedup_chunks(chunks, existing_hashes=set()) == chunks

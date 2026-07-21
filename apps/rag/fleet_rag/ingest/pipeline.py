"""Ingestion pipeline orchestration (task 3.1): extract -> OCR -> PII scan
-> structure-aware chunk -> dedup by sha -> embed (utility/embeddings role
via the gateway client) -> Qdrant upsert with metadata.

Every I/O dependency (LLM client, Qdrant, OCR) is injected so the pure
sequencing here is unit-testable without Docker or a network call; the arq
task in worker.py wires the real MinIO/LLMClient/Qdrant/DB instances and is
covered by tests/integration/test_rag_ingest_live.py.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from fleet_rag.ingest.chunk import chunk_text, dedup_chunks
from fleet_rag.ingest.extract import extract_text
from fleet_rag.ingest.pii import apply_pii_policy
from fleet_rag.store.qdrant_store import point_id_for


class EmbeddingClient(Protocol):
    async def embeddings(
        self, texts: list[str], **kwargs: Any
    ) -> Any: ...


class QdrantSink(Protocol):
    def ensure_collection(self, name: str, *, vector_size: int) -> None: ...

    def upsert(self, name: str, *, points: list[dict[str, Any]]) -> None: ...


OcrFn = Callable[[bytes], Awaitable[str]]


@dataclass(frozen=True)
class PersistedChunk:
    """A chunk that was embedded and upserted — what the caller persists to Postgres."""

    content_sha256: str
    qdrant_point_id: str
    tokens: int
    redacted: bool
    original_sensitivity: str | None


@dataclass(frozen=True)
class IngestOutcome:
    chunks_embedded: int
    chunks_skipped: int
    chunks_blocked: int
    used_ocr: bool
    persisted_chunks: list[PersistedChunk] = field(default_factory=list)


async def run_ingestion(
    *,
    data: bytes,
    filename: str,
    collection_id: int,
    sensitivity: str,
    pii_policy: str,
    llm_client: EmbeddingClient,
    qdrant: QdrantSink,
    existing_hashes: set[str],
    ocr_fn: OcrFn | None = None,
    document_id: int = 0,
) -> IngestOutcome:
    """Run the full ingest pipeline for one uploaded file's bytes."""
    extracted = extract_text(data, filename=filename)
    used_ocr = False
    text = extracted.text

    if extracted.needs_ocr:
        used_ocr = True
        text = await ocr_fn(data) if ocr_fn is not None else ""

    all_chunks = chunk_text(text)
    fresh_chunks = dedup_chunks(all_chunks, existing_hashes=existing_hashes)
    skipped = len(all_chunks) - len(fresh_chunks)

    policies = [apply_pii_policy(c.content, policy=pii_policy) for c in fresh_chunks]
    blocked = sum(1 for p in policies if p.blocked)
    keep = [
        (chunk, policy)
        for chunk, policy in zip(fresh_chunks, policies, strict=True)
        if not policy.blocked
    ]

    if not keep:
        return IngestOutcome(
            chunks_embedded=0, chunks_skipped=skipped, chunks_blocked=blocked, used_ocr=used_ocr
        )

    texts_to_embed = [policy.text for _chunk, policy in keep]
    embed_sensitivity = "pii" if any(p.local_only for _c, p in keep) else sensitivity
    response = await llm_client.embeddings(texts_to_embed, sensitivity=embed_sensitivity)

    collection_name = f"fleet_{collection_id}"
    vector_size = len(response.vectors[0])
    qdrant.ensure_collection(collection_name, vector_size=vector_size)

    points = []
    persisted: list[PersistedChunk] = []
    for (chunk, policy), vector in zip(keep, response.vectors, strict=True):
        original_sensitivity = sensitivity if policy.redacted else None
        points.append(
            {
                "content_sha256": chunk.content_sha256,
                "vector": vector,
                "payload": {
                    "document_id": document_id,
                    "content_sha256": chunk.content_sha256,
                    "content": policy.text,
                    "redacted": policy.redacted,
                    "original_sensitivity": original_sensitivity,
                },
            }
        )
        persisted.append(
            PersistedChunk(
                content_sha256=chunk.content_sha256,
                qdrant_point_id=point_id_for(chunk.content_sha256),
                tokens=len(policy.text.split()),
                redacted=policy.redacted,
                original_sensitivity=original_sensitivity,
            )
        )
    qdrant.upsert(collection_name, points=points)

    return IngestOutcome(
        chunks_embedded=len(keep), chunks_skipped=skipped, chunks_blocked=blocked,
        used_ocr=used_ocr, persisted_chunks=persisted,
    )

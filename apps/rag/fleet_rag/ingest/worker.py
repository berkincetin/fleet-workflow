"""arq worker: the `ingest_document` task and process entrypoint (task 3.1).

Wires the real dependencies (LLMClient via core.llm.factory, MinIO, Qdrant,
Postgres) around the pure `run_ingestion` orchestration in pipeline.py. Vision
OCR goes through the same governed LLMClient (CLAUDE.md rule 1 — no direct
provider SDK calls); tesseract is the local fallback (ocr.py).
"""

from __future__ import annotations

import os
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from core.llm.client import LLMClient
from core.llm.factory import build_client
from fleet_rag.ingest.ocr import OcrResult, ocr_image, tesseract_ocr
from fleet_rag.ingest.pipeline import run_ingestion
from fleet_rag.store.minio_store import minio_client_from_env
from fleet_rag.store.qdrant_store import (
    ensure_collection as qdrant_ensure_collection,
)
from fleet_rag.store.qdrant_store import (
    qdrant_client_from_env,
)
from fleet_rag.store.qdrant_store import (
    upsert_chunks as qdrant_upsert_chunks,
)
from qdrant_client import QdrantClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker


class _QdrantSinkAdapter:
    """Adapts qdrant_store's free functions to the pipeline's QdrantSink protocol."""

    def __init__(self, client: QdrantClient) -> None:
        self._client = client

    def ensure_collection(self, name: str, *, vector_size: int) -> None:
        qdrant_ensure_collection(self._client, name, vector_size=vector_size)

    def upsert(self, name: str, *, points: list[dict[str, Any]]) -> None:
        qdrant_upsert_chunks(self._client, name, points=points)


async def _existing_hashes(
    session_factory: async_sessionmaker[Any], *, document_id: int
) -> set[str]:
    async with session_factory() as session:
        rows = await session.execute(
            text("SELECT content_sha256 FROM chunks WHERE document_id = :doc"),
            {"doc": document_id},
        )
        return {r[0] for r in rows}


async def _record_chunks(
    session_factory: async_sessionmaker[Any],
    *,
    document_id: int,
    chunks: list[dict[str, Any]],
) -> None:
    if not chunks:
        return
    async with session_factory() as session:
        for c in chunks:
            await session.execute(
                text(
                    "INSERT INTO chunks (document_id, content_sha256, qdrant_point_id, "
                    "tokens, redacted, original_sensitivity) VALUES "
                    "(:doc, :sha, :point, :tokens, :redacted, :orig_sens) "
                    "ON CONFLICT DO NOTHING"
                ),
                {
                    "doc": document_id,
                    "sha": c["content_sha256"],
                    "point": c["qdrant_point_id"],
                    "tokens": c["tokens"],
                    "redacted": c["redacted"],
                    "orig_sens": c["original_sensitivity"],
                },
            )
        await session.commit()


async def _update_document_status(
    session_factory: async_sessionmaker[Any], *, document_id: int, status: str, ocr_status: str
) -> None:
    async with session_factory() as session:
        await session.execute(
            text(
                "UPDATE documents SET status = :status, ocr_status = :ocr_status "
                "WHERE id = :doc"
            ),
            {"status": status, "ocr_status": ocr_status, "doc": document_id},
        )
        await session.commit()


async def ingest_document(
    ctx: dict[str, Any],
    *,
    document_id: int,
    collection_id: int,
    object_key: str,
    filename: str,
    sensitivity: str,
    pii_policy: str,
) -> dict[str, Any]:
    """arq task: fetch the uploaded object, run the ingestion pipeline, persist chunks."""
    session_factory: async_sessionmaker[Any] = ctx["session_factory"]
    llm_client: LLMClient = ctx["llm_client"]
    minio = ctx["minio_client"]
    qdrant_sink = ctx["qdrant_sink"]
    bucket = ctx["minio_bucket"]

    data = minio.get_object(bucket, object_key).read()
    existing = await _existing_hashes(session_factory, document_id=document_id)

    async def _ocr_fn(image_bytes: bytes) -> str:
        result: OcrResult = await ocr_image(
            image_bytes,
            vision_client=llm_client,
            tesseract_fn=tesseract_ocr,
            sensitivity=sensitivity,
        )
        return str(result.text)

    try:
        outcome = await run_ingestion(
            data=data,
            filename=filename,
            collection_id=collection_id,
            sensitivity=sensitivity,
            pii_policy=pii_policy,
            llm_client=llm_client,
            qdrant=qdrant_sink,
            existing_hashes=existing,
            ocr_fn=_ocr_fn,
            document_id=document_id,
        )
    except Exception:
        await _update_document_status(
            session_factory, document_id=document_id, status="error", ocr_status="error"
        )
        raise

    await _record_chunks(
        session_factory,
        document_id=document_id,
        chunks=[
            {
                "content_sha256": c.content_sha256,
                "qdrant_point_id": c.qdrant_point_id,
                "tokens": c.tokens,
                "redacted": c.redacted,
                "original_sensitivity": c.original_sensitivity,
            }
            for c in outcome.persisted_chunks
        ],
    )
    await _update_document_status(
        session_factory,
        document_id=document_id,
        status="ready",
        ocr_status="done" if outcome.used_ocr else "not_needed",
    )
    return {
        "chunks_embedded": outcome.chunks_embedded,
        "chunks_skipped": outcome.chunks_skipped,
        "chunks_blocked": outcome.chunks_blocked,
        "used_ocr": outcome.used_ocr,
    }


async def _startup(ctx: dict[str, Any]) -> None:
    from fleet_api.db import get_engine
    from fleet_api.db import session_factory as make_session_factory

    ctx["session_factory"] = make_session_factory(get_engine())
    ctx["llm_client"] = await build_client()
    ctx["minio_client"] = minio_client_from_env()
    ctx["minio_bucket"] = os.environ.get("FLEET_MINIO_BUCKET", "fleet-documents")
    ctx["qdrant_sink"] = _QdrantSinkAdapter(qdrant_client_from_env())


async def _shutdown(ctx: dict[str, Any]) -> None:
    pass


class WorkerSettings:
    functions = [ingest_document]
    on_startup = _startup
    on_shutdown = _shutdown
    # Nightly retention purge (TRD §8): chunks+files+vectors past their
    # collection's retention_days.
    cron_jobs = [cron("fleet_rag.ingest.retention.purge_expired_cron", hour=3, minute=0)]
    redis_settings = RedisSettings.from_dsn(
        os.environ.get("FLEET_REDIS_URL", "redis://localhost:6379/1")
    )


if __name__ == "__main__":  # pragma: no cover
    from arq import run_worker

    # arq's WorkerSettingsType stub wants WorkerSettingsBase; a plain class matching
    # its documented attribute protocol is arq's own standard usage pattern.
    run_worker(WorkerSettings)  # type: ignore[arg-type]

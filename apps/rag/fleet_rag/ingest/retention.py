"""Retention purge job (task 3.2, TRD §8: per-collection retention days; the
worker purges chunks+files+vectors).

`is_expired` is the pure boundary check; `purge_expired` drives it against
the real DB/MinIO/Qdrant (all injected so the orchestration stays testable),
deleting each expired document's Qdrant points, MinIO object, and Postgres
rows (chunks then the document itself) in that order — vectors and blobs
first so a mid-purge crash never leaves a DB row pointing at deleted data.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker


def is_expired(
    *, created_at: dt.datetime, retention_days: int | None, now: dt.datetime
) -> bool:
    """No retention_days set means the collection is retained forever."""
    if retention_days is None:
        return False
    return now - created_at >= dt.timedelta(days=retention_days)


class ObjectStore(Protocol):
    def remove_object(self, bucket: str, object_key: str) -> None: ...


class VectorStore(Protocol):
    def delete_by_document(self, collection_name: str, *, document_id: int) -> None: ...


@dataclass(frozen=True)
class PurgeReport:
    purged_document_ids: list[int]


async def purge_expired(
    session_factory: async_sessionmaker[Any],
    *,
    object_store: ObjectStore,
    vector_store: VectorStore,
    bucket: str,
    now: dt.datetime | None = None,
) -> PurgeReport:
    """Delete every document (and its chunks/file/vectors) past its
    collection's retention window."""
    now = now or dt.datetime.now(dt.UTC)

    async with session_factory() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT d.id, d.collection_id, d.uri, c.retention_days, d.created_at "
                    "FROM documents d JOIN collections c ON c.id = d.collection_id "
                    "WHERE c.retention_days IS NOT NULL"
                )
            )
        ).all()

    purged: list[int] = []
    for document_id, collection_id, uri, retention_days, created_at in rows:
        if not is_expired(created_at=created_at, retention_days=retention_days, now=now):
            continue

        vector_store.delete_by_document(f"fleet_{collection_id}", document_id=document_id)
        try:
            object_store.remove_object(bucket, uri)
        except Exception:
            pass  # object already gone is not fatal to the purge

        async with session_factory() as session:
            await session.execute(
                text("DELETE FROM chunks WHERE document_id = :doc"), {"doc": document_id}
            )
            await session.execute(
                text("DELETE FROM documents WHERE id = :doc"), {"doc": document_id}
            )
            await session.commit()
        purged.append(document_id)

    return PurgeReport(purged_document_ids=purged)


async def purge_expired_cron(ctx: dict[str, Any]) -> dict[str, Any]:
    """arq cron entrypoint (registered in worker.py's WorkerSettings)."""
    from fleet_rag.store.minio_store import minio_client_from_env
    from fleet_rag.store.qdrant_store import delete_by_document, qdrant_client_from_env

    session_factory = ctx["session_factory"]
    bucket = ctx["minio_bucket"]
    minio = ctx.get("minio_client") or minio_client_from_env()
    qdrant = ctx.get("qdrant_client") or qdrant_client_from_env()

    class _VectorAdapter:
        def delete_by_document(self, collection_name: str, *, document_id: int) -> None:
            delete_by_document(qdrant, collection_name, document_id=document_id)

    report = await purge_expired(
        session_factory,
        object_store=minio,
        vector_store=_VectorAdapter(),
        bucket=bucket,
    )
    return {"purged_document_ids": report.purged_document_ids}

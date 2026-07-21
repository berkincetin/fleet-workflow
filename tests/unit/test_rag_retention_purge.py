"""purge_expired orchestration against a fake Postgres session (task 3.2).

Exercises the SELECT-then-delete sequencing (vectors+file before rows) with
an in-memory fake session/session_factory so no real DB is needed; the live
end-to-end purge (real Postgres/MinIO/Qdrant) is covered in
tests/integration/test_rag_retention_live.py.
"""

from __future__ import annotations

import datetime as dt

from fleet_rag.ingest.retention import PurgeReport, purge_expired


class _FakeSelectResult:
    """Mirrors SQLAlchemy's Result: execute() is awaited, .all() on the
    returned Result is a plain sync call."""

    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows

    def all(self):  # type: ignore[no-untyped-def]
        return self._rows


class _FakeSession:
    def __init__(self, harness: _FakeSessionFactory) -> None:
        self._harness = harness

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def execute(self, stmt, params=None):  # type: ignore[no-untyped-def]
        sql = str(stmt)
        if "SELECT d.id" in sql:
            return _FakeSelectResult(self._harness.rows)
        if "DELETE FROM chunks" in sql:
            self._harness.deleted_chunks_for.append(params["doc"])
        elif "DELETE FROM documents" in sql:
            self._harness.deleted_documents.append(params["doc"])
        return None

    async def commit(self) -> None:
        return None


class _FakeSessionFactory:
    def __init__(self, rows: list[tuple]) -> None:
        self.rows = rows
        self.deleted_chunks_for: list[int] = []
        self.deleted_documents: list[int] = []

    def __call__(self) -> _FakeSession:
        return _FakeSession(self)


class _FakeObjectStore:
    def __init__(self) -> None:
        self.removed: list[str] = []

    def remove_object(self, bucket: str, object_key: str) -> None:
        self.removed.append(object_key)


class _FakeVectorStore:
    def __init__(self) -> None:
        self.deleted: list[tuple[str, int]] = []

    def delete_by_document(self, collection_name: str, *, document_id: int) -> None:
        self.deleted.append((collection_name, document_id))


async def test_purge_expired_deletes_only_expired_documents() -> None:
    now = dt.datetime(2026, 2, 1, tzinfo=dt.UTC)
    old = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)  # 31 days old
    fresh = dt.datetime(2026, 1, 30, tzinfo=dt.UTC)  # 2 days old
    rows = [
        (1, 10, "10/doc1.txt", 7, old),  # expired: 7-day retention, 31 days old
        (2, 10, "10/doc2.txt", 7, fresh),  # not expired
        (3, 11, "11/doc3.txt", None, old),  # never handed to us (retention filter)
    ]
    sf = _FakeSessionFactory(rows)
    obj_store = _FakeObjectStore()
    vec_store = _FakeVectorStore()

    report = await purge_expired(
        sf, object_store=obj_store, vector_store=vec_store, bucket="fleet-documents", now=now
    )

    assert isinstance(report, PurgeReport)
    assert report.purged_document_ids == [1]
    assert obj_store.removed == ["10/doc1.txt"]
    assert vec_store.deleted == [("fleet_10", 1)]
    assert sf.deleted_chunks_for == [1]
    assert sf.deleted_documents == [1]


async def test_purge_expired_object_store_failure_does_not_abort_row_deletion() -> None:
    now = dt.datetime(2026, 2, 1, tzinfo=dt.UTC)
    old = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    rows = [(1, 10, "10/missing.txt", 7, old)]
    sf = _FakeSessionFactory(rows)
    vec_store = _FakeVectorStore()

    class _FailingObjectStore:
        def remove_object(self, bucket: str, object_key: str) -> None:
            raise Exception("NoSuchKey")

    report = await purge_expired(
        sf, object_store=_FailingObjectStore(), vector_store=vec_store,
        bucket="fleet-documents", now=now,
    )
    assert report.purged_document_ids == [1]
    assert sf.deleted_documents == [1]


async def test_purge_expired_nothing_expired_deletes_nothing() -> None:
    now = dt.datetime(2026, 2, 1, tzinfo=dt.UTC)
    fresh = dt.datetime(2026, 1, 30, tzinfo=dt.UTC)
    sf = _FakeSessionFactory([(1, 10, "10/doc1.txt", 7, fresh)])
    report = await purge_expired(
        sf, object_store=_FakeObjectStore(), vector_store=_FakeVectorStore(),
        bucket="fleet-documents", now=now,
    )
    assert report.purged_document_ids == []

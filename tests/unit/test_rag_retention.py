"""Retention purge: which documents are expired (task 3.2, TRD §8).

Pure decision logic — given a collection's retention_days and "now", decide
whether a document's created_at makes it expired. No I/O; the DB/MinIO/Qdrant
side effects (deleting rows/files/vectors) are exercised in the live
integration test, which calls this predicate to build its delete list.
"""

from __future__ import annotations

import datetime as dt

from fleet_rag.ingest.retention import is_expired


def test_no_retention_days_never_expires() -> None:
    now = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    created = dt.datetime(2020, 1, 1, tzinfo=dt.UTC)
    assert is_expired(created_at=created, retention_days=None, now=now) is False


def test_document_older_than_retention_is_expired() -> None:
    now = dt.datetime(2026, 1, 31, tzinfo=dt.UTC)
    created = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    assert is_expired(created_at=created, retention_days=20, now=now) is True


def test_document_within_retention_window_is_not_expired() -> None:
    now = dt.datetime(2026, 1, 10, tzinfo=dt.UTC)
    created = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    assert is_expired(created_at=created, retention_days=20, now=now) is False


def test_document_exactly_at_boundary_is_expired() -> None:
    now = dt.datetime(2026, 1, 21, tzinfo=dt.UTC)
    created = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    assert is_expired(created_at=created, retention_days=20, now=now) is True

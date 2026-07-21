"""Object key + sha256 helpers for the MinIO document store (task 3.1).

The real MinIO client is a thin wrapper the SDK already tests; what's worth
unit-testing here is the deterministic object-key layout and content hashing
this module owns, since the ingestion pipeline's dedup-by-sha AC depends on
the hash being computed the same way every time.
"""

from __future__ import annotations

from fleet_rag.store.minio_store import object_key, sha256_bytes


def test_object_key_is_deterministic_and_namespaced_by_collection() -> None:
    key = object_key(collection_id=7, sha256="abc123", filename="report.pdf")
    assert key == "7/abc123.pdf"


def test_object_key_preserves_extension_case_insensitively() -> None:
    key = object_key(collection_id=1, sha256="deadbeef", filename="SCAN.PNG")
    assert key.endswith(".png")


def test_sha256_bytes_is_stable() -> None:
    assert sha256_bytes(b"hello") == sha256_bytes(b"hello")


def test_sha256_bytes_differs_for_different_content() -> None:
    assert sha256_bytes(b"hello") != sha256_bytes(b"world")

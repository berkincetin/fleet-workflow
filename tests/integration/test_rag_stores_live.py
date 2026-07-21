"""Integration: MinIO + Qdrant stores against the real dev-stack containers
(task 3.1). Skips if the containers aren't reachable (`make dev` not running)
— see CLAUDE.md Task Execution Protocol step 3: exercised against the actually
running stack, not just mocks, but must not block `make test` when Docker is
down for an unrelated task.
"""

from __future__ import annotations

import uuid

import pytest
from fleet_rag.store.minio_store import DEFAULT_BUCKET, ensure_bucket, minio_client_from_env
from fleet_rag.store.qdrant_store import (
    collection_name,
    delete_by_document,
    ensure_collection,
    qdrant_client_from_env,
    search,
    upsert_chunks,
)


def _minio_up() -> bool:
    try:
        minio_client_from_env().list_buckets()
        return True
    except Exception:
        return False


def _qdrant_up() -> bool:
    try:
        qdrant_client_from_env().get_collections()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _minio_up(), reason="MinIO not reachable — start with `make dev`")
def test_minio_bucket_roundtrip() -> None:
    client = minio_client_from_env()
    ensure_bucket(client)
    assert client.bucket_exists(DEFAULT_BUCKET)

    key = f"test/{uuid.uuid4().hex}.txt"
    data = b"hello fleet rag"
    import io

    client.put_object(DEFAULT_BUCKET, key, io.BytesIO(data), length=len(data))
    fetched = client.get_object(DEFAULT_BUCKET, key).read()
    assert fetched == data
    client.remove_object(DEFAULT_BUCKET, key)


@pytest.mark.skipif(not _qdrant_up(), reason="Qdrant not reachable — start with `make dev`")
def test_qdrant_upsert_search_delete_roundtrip() -> None:
    client = qdrant_client_from_env()
    name = collection_name(999999)  # scratch collection for the test
    ensure_collection(client, name, vector_size=4)

    upsert_chunks(
        client,
        name,
        points=[
            {
                "content_sha256": "hash-a",
                "vector": [1.0, 0.0, 0.0, 0.0],
                "payload": {"document_id": 1, "content": "alpha chunk"},
            },
            {
                "content_sha256": "hash-b",
                "vector": [0.0, 1.0, 0.0, 0.0],
                "payload": {"document_id": 2, "content": "beta chunk"},
            },
        ],
    )

    results = search(client, name, query_vector=[1.0, 0.0, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0].payload["content"] == "alpha chunk"

    delete_by_document(client, name, document_id=1)
    results_after = search(client, name, query_vector=[1.0, 0.0, 0.0, 0.0], top_k=5)
    assert all(r.payload["document_id"] != 1 for r in results_after)

    client.delete_collection(name)

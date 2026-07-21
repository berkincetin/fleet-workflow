"""Qdrant vector store (TRD §3 tech stack, tasks 3.1/3.3).

One Qdrant collection per Fleet collection (`fleet_{collection_id}`), storing
chunk embeddings with payload metadata used by both ingestion (dedup,
retention purge) and query (hybrid retrieval, citations): document_id,
chunk_id, content, redacted, original_sensitivity.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchText,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)


def qdrant_client_from_env() -> QdrantClient:
    url = os.environ.get("FLEET_QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=url)


def collection_name(fleet_collection_id: int) -> str:
    return f"fleet_{fleet_collection_id}"


def point_id_for(content_sha256: str) -> str:
    """Deterministic point ID so re-embedding the same content upserts in place."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, content_sha256))


def ensure_collection(client: QdrantClient, name: str, *, vector_size: int) -> None:
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        # Full-text index on chunk content — the keyword half of hybrid
        # retrieval (task 3.3, dense + keyword filter).
        client.create_payload_index(
            collection_name=name, field_name="content", field_schema=PayloadSchemaType.TEXT
        )


def upsert_chunks(
    client: QdrantClient,
    name: str,
    *,
    points: list[dict[str, Any]],
) -> None:
    """points: [{content_sha256, vector, payload}, ...]"""
    client.upsert(
        collection_name=name,
        points=[
            PointStruct(
                id=point_id_for(p["content_sha256"]),
                vector=p["vector"],
                payload=p["payload"],
            )
            for p in points
        ],
    )


def search(
    client: QdrantClient,
    name: str,
    *,
    query_vector: list[float],
    top_k: int = 5,
    document_ids: list[int] | None = None,
) -> list[Any]:
    query_filter = None
    if document_ids:
        query_filter = Filter(
            should=[
                FieldCondition(key="document_id", match=MatchValue(value=d))
                for d in document_ids
            ]
        )
    return client.query_points(
        collection_name=name,
        query=query_vector,
        limit=top_k,
        query_filter=query_filter,
    ).points


def search_hybrid(
    client: QdrantClient,
    name: str,
    *,
    query_vector: list[float],
    top_k: int = 5,
    keyword: str | None = None,
) -> list[Any]:
    """Dense kNN search narrowed by an optional keyword (full-text) filter on
    chunk content — the hybrid retrieval mode for task 3.3."""
    query_filter = None
    if keyword:
        query_filter = Filter(must=[FieldCondition(key="content", match=MatchText(text=keyword))])
    return client.query_points(
        collection_name=name,
        query=query_vector,
        limit=top_k,
        query_filter=query_filter,
    ).points


def delete_by_document(client: QdrantClient, name: str, *, document_id: int) -> None:
    client.delete(
        collection_name=name,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )

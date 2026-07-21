"""Integration: retention purge against the real dev-stack (task 3.2 AC).

AC: purge removes expired chunks/files/vectors. Seeds a document with chunks
directly (bypassing the ingestion pipeline — that path is covered by
test_rag_ingest_live.py) into a collection with a 0-day retention window, then
runs purge_expired against the real Postgres/MinIO/Qdrant and asserts every
trace of the document is gone.

Also covers the Collections API's GET path live (creation requires
MANAGE_DEPT, which no seeded dev-realm user currently holds — a pre-existing
role-naming gap between the Keycloak realm seed and rbac.py, not something to
patch here); the collection row itself is inserted directly for the purge
scenario.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import uuid

import httpx
import psycopg2
import pytest
from minio.error import S3Error

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
SYNC_DATABASE_URL = "postgresql://fleet:fleet_dev_pw@localhost:5432/fleet"


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _stack_up(), reason="dev stack not reachable — start with `make dev`"
)


def _builder_token() -> str:
    resp = httpx.post(
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "client_secret": "fleet-api-dev-secret",
            "grant_type": "password",
            "username": "builder",
            "password": "builder",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


def test_collections_list_endpoint_live() -> None:
    import asyncio
    import os

    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"

    from fleet_api.app import create_app

    token = _builder_token()

    async def _run() -> httpx.Response:
        import fleet_api.db as fleet_db

        # See test_rag_pii_collection_live.py for why this is required across
        # test modules on Windows (cached engine bound to a closed event loop).
        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(
                "/v1/collections", headers={"Authorization": f"Bearer {token}"}
            )

    resp = asyncio.run(_run())
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_purge_expired_removes_chunks_files_and_vectors() -> None:
    from fleet_rag.store.minio_store import minio_client_from_env
    from fleet_rag.store.qdrant_store import (
        collection_name,
        ensure_collection,
        point_id_for,
        qdrant_client_from_env,
        upsert_chunks,
    )

    name = f"retention-live-test-{uuid.uuid4().hex[:8]}"
    conn = psycopg2.connect(SYNC_DATABASE_URL)
    try:
        with conn.cursor() as cur:
            # 0-day retention: created_at "now" is already expired (>= 0 days).
            cur.execute(
                "INSERT INTO collections (name, sensitivity, pii_policy, retention_days) "
                "VALUES (%s, 'internal', 'redact', 0) RETURNING id",
                (name,),
            )
            collection_id = cur.fetchone()[0]

            data = b"retention purge smoke test content"
            digest = hashlib.sha256(data).hexdigest()
            key = f"{collection_id}/{digest}.txt"

            minio = minio_client_from_env()
            if not minio.bucket_exists("fleet-documents"):
                minio.make_bucket("fleet-documents")
            minio.put_object("fleet-documents", key, io.BytesIO(data), length=len(data))

            old_created_at = dt.datetime.now(dt.UTC) - dt.timedelta(days=1)
            cur.execute(
                "INSERT INTO documents (collection_id, uri, sha256, status, created_at) "
                "VALUES (%s, %s, %s, 'ready', %s) RETURNING id",
                (collection_id, key, digest, old_created_at),
            )
            document_id = cur.fetchone()[0]

            content_sha = hashlib.sha256(b"chunk content").hexdigest()
            point_id = point_id_for(content_sha)
            cur.execute(
                "INSERT INTO chunks (document_id, content_sha256, qdrant_point_id, tokens) "
                "VALUES (%s, %s, %s, %s)",
                (document_id, content_sha, point_id, 2),
            )
            conn.commit()

        qdrant = qdrant_client_from_env()
        qname = collection_name(collection_id)
        ensure_collection(qdrant, qname, vector_size=4)
        upsert_chunks(
            qdrant,
            qname,
            points=[
                {
                    "content_sha256": content_sha,
                    "vector": [0.1, 0.2, 0.3, 0.4],
                    "payload": {"document_id": document_id, "content": "chunk content"},
                }
            ],
        )

        # Sanity: everything exists before the purge.
        assert minio.stat_object("fleet-documents", key) is not None
        pre_hits = qdrant.retrieve(qname, ids=[point_id])
        assert len(pre_hits) == 1

        import asyncio

        from fleet_api.db import get_engine
        from fleet_api.db import session_factory as make_session_factory
        from fleet_rag.ingest.retention import purge_expired

        class _VectorAdapter:
            def delete_by_document(self, cname: str, *, document_id: int) -> None:
                from fleet_rag.store.qdrant_store import delete_by_document

                delete_by_document(qdrant, cname, document_id=document_id)

        async def _run() -> None:
            sf = make_session_factory(get_engine())
            report = await purge_expired(
                sf,
                object_store=minio,
                vector_store=_VectorAdapter(),
                bucket="fleet-documents",
            )
            assert document_id in report.purged_document_ids

        asyncio.run(_run())

        # File gone from MinIO.
        with pytest.raises(S3Error):
            minio.stat_object("fleet-documents", key)

        # Vector gone from Qdrant.
        post_hits = qdrant.retrieve(qname, ids=[point_id])
        assert len(post_hits) == 0

        # Rows gone from Postgres.
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM documents WHERE id = %s", (document_id,))
            assert cur.fetchone() is None
            cur.execute("SELECT 1 FROM chunks WHERE document_id = %s", (document_id,))
            assert cur.fetchone() is None

        qdrant.delete_collection(qname)
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM collections WHERE name = %s", (name,))
            conn.commit()
        conn.close()

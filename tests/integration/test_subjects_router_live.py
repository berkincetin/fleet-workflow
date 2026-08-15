"""Integration: DELETE /v1/subjects/{hash} against the real dev-stack (task 8.3
AC: "erasure removes subject data, audit preserved pseudonymized").

Seeds one subject's conversation+message, document+chunk+MinIO object+Qdrant
vector, and an audit_log row all tied to the same subject_hash, then calls
the real endpoint and asserts every trace is gone except the audit row, which
must survive with its actor pseudonymized (never deleted, per TRD §8).
"""

from __future__ import annotations

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


def _admin_token() -> str:
    resp = httpx.post(
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "client_secret": "fleet-api-dev-secret",
            "grant_type": "password",
            "username": "admin",
            "password": "admin",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


def test_erase_subject_removes_conversation_document_and_pseudonymizes_audit() -> None:
    from fleet_api.privacy import subject_hash
    from fleet_rag.store.minio_store import minio_client_from_env
    from fleet_rag.store.qdrant_store import (
        collection_name,
        ensure_collection,
        point_id_for,
        qdrant_client_from_env,
        upsert_chunks,
    )

    kc_sub = f"erasure-live-test-{uuid.uuid4().hex[:8]}"
    hash_ = subject_hash(kc_sub)
    coll_name = f"subjects-live-test-{uuid.uuid4().hex[:8]}"

    conn = psycopg2.connect(SYNC_DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO collections (name, sensitivity, pii_policy) "
                "VALUES (%s, 'pii', 'allow-local-only') RETURNING id",
                (coll_name,),
            )
            collection_id = cur.fetchone()[0]

            data = b"erasure live test document content"
            digest = hashlib.sha256(data).hexdigest()
            key = f"{collection_id}/{digest}.txt"
            minio = minio_client_from_env()
            if not minio.bucket_exists("fleet-documents"):
                minio.make_bucket("fleet-documents")
            minio.put_object("fleet-documents", key, io.BytesIO(data), length=len(data))

            cur.execute(
                "INSERT INTO documents (collection_id, uri, sha256, status, subject_hash) "
                "VALUES (%s, %s, %s, 'ready', %s) RETURNING id",
                (collection_id, key, digest, hash_),
            )
            document_id = cur.fetchone()[0]

            # Unique per run: qdrant_point_id is deterministic from content_sha256
            # (point_id_for) and globally unique in chunks — a fixed literal here
            # would collide with a leftover row from any earlier failed/aborted run.
            chunk_text = f"erasure test chunk {uuid.uuid4().hex}"
            content_sha = hashlib.sha256(chunk_text.encode()).hexdigest()
            point_id = point_id_for(content_sha)
            cur.execute(
                "INSERT INTO chunks (document_id, content_sha256, qdrant_point_id, tokens) "
                "VALUES (%s, %s, %s, %s)",
                (document_id, content_sha, point_id, 2),
            )

            cur.execute("SELECT id FROM users WHERE kc_sub = %s", (kc_sub,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "INSERT INTO users (kc_sub, email_hash, display_name, status) "
                    "VALUES (%s, '', %s, 'active') RETURNING id",
                    (kc_sub, kc_sub),
                )
                user_id = cur.fetchone()[0]
            else:
                user_id = row[0]

            cur.execute("SELECT id FROM agents LIMIT 1")
            agent_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO conversations (agent_id, user_id, subject_hash) "
                "VALUES (%s, %s, %s) RETURNING id",
                (agent_id, user_id, hash_),
            )
            conv_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO messages (conv_id, role, content) VALUES (%s, 'user', %s)",
                (conv_id, "erasure live test message"),
            )
            cur.execute(
                "INSERT INTO audit_log (actor, actor_type, action, entity, entity_id) "
                "VALUES (%s, 'user', 'test.action', 'test_entity', %s)",
                (kc_sub, str(document_id)),
            )
            conn.commit()

        qdrant = qdrant_client_from_env()
        qname = collection_name(collection_id)
        ensure_collection(qdrant, qname, vector_size=4)
        upsert_chunks(
            qdrant, qname,
            points=[
                {
                    "content_sha256": content_sha, "vector": [0.1, 0.2, 0.3, 0.4],
                    "payload": {"document_id": document_id, "content": "erasure test chunk"},
                }
            ],
        )

        import asyncio
        import os

        os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
        os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
        os.environ["FLEET_OIDC_JWKS_URL"] = (
            f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
        )
        os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"

        from fleet_api.app import create_app

        token = _admin_token()

        async def _run() -> httpx.Response:
            import fleet_api.db as fleet_db

            fleet_db._app_session_factory.cache_clear()
            app = create_app(with_middleware=False)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.delete(
                    f"/v1/subjects/{hash_}", headers={"Authorization": f"Bearer {token}"}
                )

        resp = asyncio.run(_run())
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["conversations_deleted"] == 1
        assert body["messages_deleted"] == 1
        assert body["documents_deleted"] == 1
        assert body["audit_rows_pseudonymized"] == 1

        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM conversations WHERE id = %s", (conv_id,))
            assert cur.fetchone() is None
            cur.execute("SELECT 1 FROM messages WHERE conv_id = %s", (conv_id,))
            assert cur.fetchone() is None
            cur.execute("SELECT 1 FROM documents WHERE id = %s", (document_id,))
            assert cur.fetchone() is None
            cur.execute("SELECT 1 FROM chunks WHERE document_id = %s", (document_id,))
            assert cur.fetchone() is None

            # Audit row survives, but its actor no longer identifies the subject.
            cur.execute(
                "SELECT actor FROM audit_log WHERE entity_id = %s AND action = 'test.action'",
                (str(document_id),),
            )
            audit_row = cur.fetchone()
            assert audit_row is not None, "audit row must be preserved, not deleted"
            assert audit_row[0] != kc_sub
            assert hash_[:16] in audit_row[0]

        with pytest.raises(S3Error):
            minio.stat_object("fleet-documents", key)
        post_hits = qdrant.retrieve(qname, ids=[point_id])
        assert len(post_hits) == 0

        qdrant.delete_collection(qname)
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM audit_log WHERE actor LIKE %s", (f"%{hash_[:16]}%",))
            cur.execute("DELETE FROM conversations WHERE subject_hash = %s", (hash_,))
            cur.execute("DELETE FROM documents WHERE subject_hash = %s", (hash_,))
            cur.execute("DELETE FROM users WHERE kc_sub = %s", (kc_sub,))
            cur.execute("DELETE FROM collections WHERE name = %s", (coll_name,))
            conn.commit()
        conn.close()

"""Integration: document upload -> arq ingestion -> Qdrant, end to end against
the real dev-stack (task 3.1 AC). Skips if the stack (`make dev`) isn't up.

Uses the seeded `builder` user (has UPLOAD permission, TRD §7.1) against the
live dev Keycloak realm; a scratch `collections` row is inserted directly
(the Collections API itself is task 3.2). The arq job is run inline via
`ingest_document` (not through a worker process) so the test stays fast and
deterministic while still exercising the real MinIO fetch, real LLMClient ->
LiteLLM proxy embeddings call, and real Qdrant upsert.

Everything DB-touching runs inside a single asyncio.run() call using
httpx.ASGITransport (not Starlette's sync TestClient) — Starlette's TestClient
spins a fresh event loop per synchronous call on Windows, and the API's
process-wide cached asyncpg connection pool (fleet_api.db._app_session_factory)
does not tolerate being reused across event loop boundaries there.
"""

from __future__ import annotations

import os

import httpx
import psycopg2
import pytest

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


@pytest.fixture(scope="module")
def collection_id() -> int:
    # Plain sync psycopg2 — keeps fixture setup off the async engine entirely.
    # A fresh collection per test run (rather than upserting a fixed name) keeps
    # runs isolated: the documents table's unique (collection_id, sha256) index
    # would otherwise resolve this run's upload to a previous run's leftover row.
    import uuid

    conn = psycopg2.connect(SYNC_DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO collections (name, sensitivity, pii_policy) "
                "VALUES (%s, 'internal', 'redact') RETURNING id",
                (f"sprint3-live-test-{uuid.uuid4().hex[:8]}",),
            )
            row = cur.fetchone()
            conn.commit()
            assert row is not None
            return int(row[0])
    finally:
        conn.close()


def test_upload_document_ingests_and_lands_in_qdrant(collection_id: int) -> None:
    import asyncio

    from fleet_rag.store.qdrant_store import collection_name, qdrant_client_from_env, search

    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"

    token = _builder_token()

    async def _run() -> dict:
        import fleet_api.db as fleet_db
        from core.llm.factory import build_client
        from fleet_api.app import create_app
        from fleet_api.db import get_engine
        from fleet_api.db import session_factory as make_session_factory
        from fleet_rag.ingest.worker import _QdrantSinkAdapter, ingest_document
        from fleet_rag.store.minio_store import minio_client_from_env

        # See test_rag_pii_collection_live.py for why this is required across
        # test modules on Windows (cached engine bound to a closed event loop).
        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)
        headers = {"Authorization": f"Bearer {token}"}
        upload_text = ("integration " * 50 + "\n\n" + "test content " * 50).encode()

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/v1/documents?collection_id={collection_id}",
                files={"file": ("sprint3.txt", upload_text, "text/plain")},
                headers=headers,
            )
            assert resp.status_code == 201, resp.text
            doc = resp.json()
            assert doc["status"] == "queued"
            document_id = doc["id"]

            # Re-upload the identical bytes: resolves to the same document (0 new
            # embeddings, AC 3.1) rather than creating a second row.
            resp2 = await client.post(
                f"/v1/documents?collection_id={collection_id}",
                files={"file": ("sprint3.txt", upload_text, "text/plain")},
                headers=headers,
            )
            assert resp2.status_code == 201, resp2.text
            assert resp2.json()["id"] == document_id

            # Run the ingestion task inline (real MinIO fetch, real LLMClient
            # embed call through the LiteLLM proxy, real Qdrant upsert).
            sf = make_session_factory(get_engine())
            ctx = {
                "session_factory": sf,
                "llm_client": await build_client(),
                "minio_client": minio_client_from_env(),
                "minio_bucket": "fleet-documents",
                "qdrant_sink": _QdrantSinkAdapter(qdrant_client_from_env()),
            }
            result = await ingest_document(
                ctx,
                document_id=document_id,
                collection_id=collection_id,
                object_key=doc["uri"],
                filename="sprint3.txt",
                sensitivity="internal",
                pii_policy="redact",
            )

            status_resp = await client.get(f"/v1/documents/{document_id}", headers=headers)
            return {"result": result, "document_id": document_id, "status": status_resp.json()}

    outcome = asyncio.run(_run())
    assert outcome["result"]["chunks_embedded"] >= 1
    assert outcome["status"]["status"] == "ready"

    qc = qdrant_client_from_env()
    hits = search(qc, collection_name(collection_id), query_vector=[0.0] * 1536, top_k=10)
    assert any(h.payload.get("document_id") == outcome["document_id"] for h in hits)

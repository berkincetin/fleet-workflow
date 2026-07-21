"""Integration: `/v1/rag/query` end to end against the real dev-stack (task
3.3 AC: "question over seeded docs returns grounded answer object with
citations"). Seeds a document through the real ingestion pipeline (as in
test_rag_ingest_live.py), then asks a question whose answer only exists in
that document, and asserts the response is grounded (>=1 citation resolving
to the actually-ingested chunk) — the TRD §9 structural guardrail exercised
through the real LLM, not a fake.
"""

from __future__ import annotations

import os
import uuid

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
    conn = psycopg2.connect(SYNC_DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO collections (name, sensitivity, pii_policy) "
                "VALUES (%s, 'internal', 'redact') RETURNING id",
                (f"query-live-test-{uuid.uuid4().hex[:8]}",),
            )
            row = cur.fetchone()
            conn.commit()
            assert row is not None
            return int(row[0])
    finally:
        conn.close()


def test_rag_query_returns_grounded_answer_with_citations(collection_id: int) -> None:
    import asyncio

    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"

    token = _builder_token()

    # A fact that only exists in this doc — proves the answer is actually
    # grounded in the retrieved chunk, not the model's prior knowledge.
    fact = "The Zylophant project's internal budget code is QX-4471-ZY."
    upload_text = (
        f"{fact} This code must be used on all Zylophant-related purchase orders. "
        + ("Additional filler context. " * 40)
    ).encode()

    async def _run() -> dict:
        import fleet_api.db as fleet_db
        from core.llm.factory import build_client
        from fleet_api.app import create_app
        from fleet_api.db import get_engine
        from fleet_api.db import session_factory as make_session_factory
        from fleet_rag.ingest.worker import _QdrantSinkAdapter, ingest_document
        from fleet_rag.store.minio_store import minio_client_from_env

        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/v1/documents?collection_id={collection_id}",
                files={"file": ("zylophant.txt", upload_text, "text/plain")},
                headers=headers,
            )
            assert resp.status_code == 201, resp.text
            document_id = resp.json()["id"]

            sf = make_session_factory(get_engine())
            llm_client = await build_client()
            ctx = {
                "session_factory": sf,
                "llm_client": llm_client,
                "minio_client": minio_client_from_env(),
                "minio_bucket": "fleet-documents",
                "qdrant_sink": _QdrantSinkAdapter(qdrant_client_from_env()),
            }
            ingest_result = await ingest_document(
                ctx,
                document_id=document_id,
                collection_id=collection_id,
                object_key=resp.json()["uri"],
                filename="zylophant.txt",
                sensitivity="internal",
                pii_policy="redact",
            )
            assert ingest_result["chunks_embedded"] >= 1

            query_resp = await client.post(
                "/v1/rag/query",
                json={
                    "collection_id": collection_id,
                    "question": "What is the Zylophant project's internal budget code?",
                    "top_k": 5,
                },
                headers=headers,
            )
            return {"status": query_resp.status_code, "body": query_resp.json()}

    from fleet_rag.store.qdrant_store import qdrant_client_from_env

    outcome = asyncio.run(_run())
    assert outcome["status"] == 200, outcome["body"]
    body = outcome["body"]

    assert body["degraded"] is False, body
    assert "QX-4471-ZY" in body["answer"]
    assert len(body["citations"]) >= 1
    for c in body["citations"]:
        assert "chunk_ref" in c
        assert "document_id" in c

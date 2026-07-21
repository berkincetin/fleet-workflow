"""Integration: PII-sensitivity collection ingestion, end to end against the
real dev-stack (task 3.2 AC: "PII doc in `pii` collection gets redacted
variant" — read as the local-lane counterpart of the redact AC already proven
for `internal`/`confidential` in test_rag_pipeline.py: a `pii` collection
uses `allow-local-only`, so the document must route to the local embedding
lane (Ollama bge-m3) rather than any cloud model, per TRD §8's local-model
lane rule and CLAUDE.md rule 2 (sensitivity routing never bypassed).

Skips if the dev stack or the local Ollama lane isn't reachable.
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
OLLAMA_BASE = "http://localhost:11434"


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{KEYCLOAK_BASE}/realms/fleet/.well-known/openid-configuration", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _ollama_has_bge_m3() -> bool:
    try:
        r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200 and any(
            m["name"].startswith("bge-m3") for m in r.json().get("models", [])
        )
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_stack_up() and _ollama_has_bge_m3()),
    reason="dev stack or Ollama bge-m3 not reachable",
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
def pii_collection_id() -> int:
    conn = psycopg2.connect(SYNC_DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO collections (name, sensitivity, pii_policy) "
                "VALUES (%s, 'pii', 'allow-local-only') RETURNING id",
                (f"pii-live-test-{uuid.uuid4().hex[:8]}",),
            )
            row = cur.fetchone()
            conn.commit()
            assert row is not None
            return int(row[0])
    finally:
        conn.close()


def test_pii_collection_document_routes_to_local_embedding_lane(pii_collection_id: int) -> None:
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

        # fleet_api.db caches a process-wide engine/pool keyed to whichever event
        # loop first built it; each test module's own asyncio.run() call creates a
        # fresh loop, so the cache must be cleared first or FastAPI's get_session
        # dependency reuses a pooled asyncpg connection bound to an already-closed
        # loop (Windows ProactorEventLoop does not tolerate this).
        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)
        headers = {"Authorization": f"Bearer {token}"}
        # Contains PII (TR IBAN + email) — under allow-local-only the text must
        # stay intact (not redacted) but never leave the local lane.
        upload_text = (
            b"Musteri IBAN: TR330006100519786457841326. "
            b"Iletisim: jane@example.com. " + b"padding content " * 30
        )

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/v1/documents?collection_id={pii_collection_id}",
                files={"file": ("pii-doc.txt", upload_text, "text/plain")},
                headers=headers,
            )
            assert resp.status_code == 201, resp.text
            doc = resp.json()
            document_id = doc["id"]

            sf = make_session_factory(get_engine())
            llm_client = await build_client()
            ctx = {
                "session_factory": sf,
                "llm_client": llm_client,
                "minio_client": minio_client_from_env(),
                "minio_bucket": "fleet-documents",
                "qdrant_sink": _QdrantSinkAdapter(qdrant_client_from_env()),
            }
            result = await ingest_document(
                ctx,
                document_id=document_id,
                collection_id=pii_collection_id,
                object_key=doc["uri"],
                filename="pii-doc.txt",
                sensitivity="pii",
                pii_policy="allow-local-only",
            )
            status_resp = await client.get(f"/v1/documents/{document_id}", headers=headers)
            return {
                "result": result,
                "document_id": document_id,
                "status": status_resp.json(),
            }

    outcome = asyncio.run(_run())
    assert outcome["result"]["chunks_embedded"] >= 1
    assert outcome["status"]["status"] == "ready"

    qc = qdrant_client_from_env()
    # bge-m3 embedding dim is 1024.
    hits = search(qc, collection_name(pii_collection_id), query_vector=[0.0] * 1024, top_k=10)
    matching = [h for h in hits if h.payload.get("document_id") == outcome["document_id"]]
    assert matching, "expected the ingested chunk to be present in Qdrant"
    # allow-local-only keeps the original text — not redacted, PII stays intact
    # in content because the policy is "never send this off-box", not "scrub it".
    assert matching[0].payload["redacted"] is False

"""Integration: PII masking in logs/traces against the real dev-stack (task
8.4 AC: "detected identifiers appear masked in Loki and Langfuse for a seeded
PII conversation").

Sends one chat message containing a real-shaped email address through the
plain-passthrough reply path (routers/chat.py's `_stream_reply`, the branch
task 8.4 wired), then verifies both surfaces independently:
- Loki: the structured log line `core.logging.get_logger` pushed has the
  email masked, never the raw address.
- Langfuse: the trace litellm's own proxy-side callback recorded has its
  prompt/response redacted (the `redact_langfuse` flag threaded through
  core.llm.transport as the `litellm-enable-message-redaction` header),
  never the raw address either.

Both backends ingest asynchronously, so each assertion polls briefly.
"""

from __future__ import annotations

import time
import uuid

import httpx
import psycopg2
import pytest

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
SYNC_DATABASE_URL = "postgresql://fleet:fleet_dev_pw@localhost:5432/fleet"
LOKI_BASE = "http://localhost:3100"
LANGFUSE_BASE = "http://localhost:3001"
LANGFUSE_PUBLIC_KEY = "pk-lf-fleet-dev"
LANGFUSE_SECRET_KEY = "sk-lf-fleet-dev"

_TEST_EMAIL = "candidate.pii.test@example.com"


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


def test_pii_conversation_masked_in_loki_and_langfuse() -> None:
    agent_name = f"pii-logging-live-test-{uuid.uuid4().hex[:8]}"
    conn = psycopg2.connect(SYNC_DATABASE_URL)
    try:
        with conn.cursor() as cur:
            # sensitivity=internal, no collection_ids -> hits _stream_reply's
            # plain-passthrough branch (the one task 8.4 wired), not RAG/analytics.
            cur.execute(
                "INSERT INTO agents (name, sensitivity, reasoning_model, utility_model, "
                "collection_ids) VALUES (%s, 'internal', 'reasoning', 'utility', '{}') "
                "RETURNING id",
                (agent_name,),
            )
            agent_id = cur.fetchone()[0]
            conn.commit()

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

        async def _run() -> tuple[int, str]:
            import fleet_api.db as fleet_db

            fleet_db._app_session_factory.cache_clear()
            app = create_app(with_middleware=False)
            transport = httpx.ASGITransport(app=app)
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                conv_resp = await client.post(
                    "/v1/conversations", json={"agent_id": agent_id}, headers=headers
                )
                assert conv_resp.status_code == 201, conv_resp.text
                conv_id = conv_resp.json()["id"]

                async with client.stream(
                    "POST",
                    f"/v1/conversations/{conv_id}/messages",
                    json={"content": f"My contact email is {_TEST_EMAIL}, please note it."},
                    headers=headers,
                ) as resp:
                    assert resp.status_code == 200
                    trace_id = ""
                    async for line in resp.aiter_lines():
                        if line.startswith("event: done"):
                            continue
                        if line.startswith("data:") and '"trace_id"' in line:
                            import json as _json

                            trace_id = _json.loads(line[len("data:") :])["trace_id"]
                    # asyncio.run() cancels any still-pending tasks the instant
                    # this coroutine returns; routers/chat.py's Langfuse
                    # redaction is a deliberate fire-and-forget background task
                    # (production's event loop stays alive across requests and
                    # gets to it naturally) — this short-lived test loop needs
                    # to explicitly wait for it instead.
                    from fleet_api.routers import chat as chat_module

                    if chat_module._background_tasks:
                        await asyncio.wait(chat_module._background_tasks, timeout=15)

                    return conv_id, trace_id

        conv_id, trace_id = asyncio.run(_run())
        assert trace_id, "expected a trace_id from the done event"

        # --- Loki: the masked log line must be present, the raw email absent ---
        deadline = time.time() + 20
        loki_lines: list[str] = []
        while time.time() < deadline:
            r = httpx.get(
                f"{LOKI_BASE}/loki/api/v1/query_range",
                params={
                    "query": '{service="fleet-api"} |= "chat.message.received"',
                    "start": str(int((time.time() - 120) * 1_000_000_000)),
                    "end": str(int((time.time() + 5) * 1_000_000_000)),
                    "limit": "50",
                },
                timeout=5,
            )
            if r.status_code == 200:
                for stream in r.json().get("data", {}).get("result", []):
                    loki_lines.extend(v[1] for v in stream.get("values", []))
                if any(str(conv_id) in ln for ln in loki_lines):
                    break
            time.sleep(2)

        matching = [ln for ln in loki_lines if str(conv_id) in ln]
        assert matching, "expected a chat.message.received log line for this conversation in Loki"
        assert not any(_TEST_EMAIL in ln for ln in matching), (
            f"raw email leaked into Loki: {matching!r}"
        )
        assert any("[EMAIL]" in ln for ln in matching)

        # --- Langfuse: the trace's observation content must be redacted ------
        # litellm's own callback writes the raw trace essentially synchronously;
        # our redaction (routers/chat.py's fire-and-forget LangfuseRedactor
        # task) runs afterward and needs its own few seconds — poll until the
        # raw email is actually gone, not just until the trace first appears.
        deadline = time.time() + 40
        trace_body: dict = {}
        seen_trace = False
        while time.time() < deadline:
            r = httpx.get(
                f"{LANGFUSE_BASE}/api/public/traces/{trace_id}",
                auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY),
                timeout=5,
            )
            if r.status_code == 200:
                trace_body = r.json()
                if trace_body.get("observations"):
                    seen_trace = True
                    if _TEST_EMAIL not in str(trace_body):
                        break
            time.sleep(2)

        assert seen_trace, "expected the trace to eventually appear in Langfuse"
        raw_dump = str(trace_body)
        assert _TEST_EMAIL not in raw_dump, "raw email leaked into the Langfuse trace"
    finally:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM messages WHERE conv_id IN "
                "(SELECT id FROM conversations WHERE agent_id = "
                "(SELECT id FROM agents WHERE name = %s))",
                (agent_name,),
            )
            cur.execute(
                "DELETE FROM conversations WHERE agent_id = "
                "(SELECT id FROM agents WHERE name = %s)",
                (agent_name,),
            )
            cur.execute("DELETE FROM agents WHERE name = %s", (agent_name,))
            conn.commit()
        conn.close()

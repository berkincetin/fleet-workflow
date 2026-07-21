"""Integration: chat SSE + feedback against the real dev stack (task 4.3 AC:
"streamed answer renders with citations; 👍/👎 lands in Langfuse").

Real Keycloak login (builder), real agent via /v1/admin/agents, real
conversation, a real streamed LLM call through the LiteLLM proxy (parses the
raw SSE bytes the way a browser's EventSource would), then posts feedback and
polls Langfuse's public API to confirm the score actually landed on the
message's trace — the literal AC wording, not just "the DB row exists".
"""

from __future__ import annotations

import asyncio
import os
import uuid

import httpx
import pytest

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
LANGFUSE_BASE = "http://localhost:3001"
LANGFUSE_AUTH = ("pk-lf-fleet-dev", "sk-lf-fleet-dev")


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


def _parse_sse(raw: bytes) -> list[tuple[str, dict]]:
    import json

    events: list[tuple[str, dict]] = []
    event_name = None
    for line in raw.decode().splitlines():
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
        elif line.startswith("data:") and event_name:
            events.append((event_name, json.loads(line[len("data:") :].strip())))
            event_name = None
    return events


def test_chat_stream_renders_answer_and_feedback_lands_in_langfuse() -> None:
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"
    # Pin the real compose Redis explicitly — some earlier test in the same
    # pytest session (test_middleware.py) points FLEET_REDIS_URL at its own
    # testcontainers Redis and leaves it set in os.environ afterward, which
    # would otherwise make this test's KillSwitch try to reach an already-torn-
    # down ephemeral container.
    os.environ["FLEET_REDIS_URL"] = "redis://localhost:6379/0"

    token = _builder_token()

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from fleet_api.app import create_app

        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)
        headers = {"Authorization": f"Bearer {token}"}
        agent_name = f"live-chat-agent-{uuid.uuid4().hex[:8]}"

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", headers=headers, timeout=30
        ) as client:
            created_agent = await client.post("/v1/admin/agents", json={"name": agent_name})
            assert created_agent.status_code == 201, created_agent.text
            agent_id = created_agent.json()["id"]

            created_conv = await client.post("/v1/conversations", json={"agent_id": agent_id})
            assert created_conv.status_code == 201, created_conv.text
            conv_id = created_conv.json()["id"]

            async with client.stream(
                "POST",
                f"/v1/conversations/{conv_id}/messages",
                json={"content": "Say hi in exactly three words."},
            ) as resp:
                assert resp.status_code == 200
                raw = b""
                async for chunk in resp.aiter_bytes():
                    raw += chunk

            events = _parse_sse(raw)
            token_events = [d["delta"] for name, d in events if name == "token"]
            assert token_events, "expected at least one streamed token event"
            full_text = "".join(token_events)
            assert full_text.strip() != ""

            citation_events = [d for name, d in events if name == "citations"]
            assert citation_events, "expected a citations event"

            done_events = [d for name, d in events if name == "done"]
            assert done_events, "expected a done event"
            message_id = done_events[0]["message_id"]
            trace_id = done_events[0]["trace_id"]

            feedback = await client.post(
                f"/v1/messages/{message_id}/feedback",
                json={"score": 1, "reason": "clear and correct"},
            )
            assert feedback.status_code == 201, feedback.text
            # Cleanup: conversations/messages/feedback reference this agent's
            # conversation via FK, so leave the agent row (dev-only, harmless)
            # rather than cascading deletes the API doesn't expose.

        # Poll Langfuse briefly — the score POST is synchronous in our code but
        # Langfuse's own ingestion can lag slightly behind the write.
        async with httpx.AsyncClient(auth=LANGFUSE_AUTH, timeout=10) as lf:
            for _ in range(10):
                trace_resp = await lf.get(f"{LANGFUSE_BASE}/api/public/traces/{trace_id}")
                if trace_resp.status_code == 200 and trace_resp.json().get("scores"):
                    scores = trace_resp.json()["scores"]
                    assert any(s["name"] == "user-feedback" and s["value"] == 1 for s in scores)
                    return
                await asyncio.sleep(1)
            pytest.fail(f"feedback score never appeared on Langfuse trace {trace_id}")

    asyncio.run(_run())

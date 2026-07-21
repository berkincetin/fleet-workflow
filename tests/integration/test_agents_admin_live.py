"""Integration: `/v1/admin/agents` CRUD + pause/resume against the real dev
stack (task 4.2 AC: "a paused agent stops accepting runs within 5s").

Uses the seeded `builder` user (holds MANAGE_AGENTS per TRD §7.1's "Create/edit
agents (dept)" row) against the live Keycloak realm — unlike the Collections/
Models admin APIs (MANAGE_DEPT/MANAGE_PLATFORM), no pre-existing role gap here,
so the full CRUD + pause flow is exercised through the real HTTP API (in
process via httpx.ASGITransport, same pattern as the Sprint 3 live tests —
this environment doesn't run `make api` as a standalone server), not direct
SQL. Pause is proven live end-to-end: POST /pause -> real Redis flag set -> a
fresh core.graph run against that agent name short-circuits without calling
the model.
"""

from __future__ import annotations

import os
import uuid

import httpx
import pytest

KEYCLOAK_BASE = "http://localhost:8080"
API_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
REDIS_URL = "redis://localhost:6379/0"


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


def test_agent_crud_and_pause_blocks_a_real_graph_run() -> None:
    os.environ["FLEET_DATABASE_URL"] = API_DATABASE_URL
    os.environ["FLEET_OIDC_ISSUER"] = f"{KEYCLOAK_BASE}/realms/fleet"
    os.environ["FLEET_OIDC_JWKS_URL"] = (
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/certs"
    )
    os.environ["FLEET_OIDC_AUDIENCE"] = "fleet-api"
    # Pin the real compose Redis explicitly — see test_chat_live.py for why
    # (test_middleware.py leaves FLEET_REDIS_URL pointed at a torn-down
    # testcontainers Redis if it ran earlier in the same pytest session).
    os.environ["FLEET_REDIS_URL"] = REDIS_URL

    token = _builder_token()

    async def _run() -> None:
        import fleet_api.db as fleet_db
        from core.graph import AgentSpec, build_graph
        from core.killswitch import KillSwitch
        from fleet_api.app import create_app
        from langgraph.checkpoint.memory import InMemorySaver
        from redis.asyncio import Redis

        # See test_rag_pii_collection_live.py for why this is required across
        # test modules on Windows (cached engine bound to a closed event loop).
        fleet_db._app_session_factory.cache_clear()

        app = create_app(with_middleware=False)
        transport = httpx.ASGITransport(app=app)
        headers = {"Authorization": f"Bearer {token}"}
        name = f"live-agent-{uuid.uuid4().hex[:8]}"

        async with httpx.AsyncClient(
            transport=transport, base_url="http://test", headers=headers
        ) as client:
            created = await client.post("/v1/admin/agents", json={"name": name})
            assert created.status_code == 201, created.text
            agent_id = created.json()["id"]
            assert created.json()["status"] == "active"

            listed = await client.get("/v1/admin/agents")
            assert listed.status_code == 200
            assert any(a["id"] == agent_id for a in listed.json())

            paused = await client.post(f"/v1/admin/agents/{agent_id}/pause")
            assert paused.status_code == 204

            got = await client.get(f"/v1/admin/agents/{agent_id}")
            assert got.json()["status"] == "paused"

            # The real enforcement point: a fresh graph run for this agent name,
            # built against the SAME Redis the API just wrote to, must
            # short-circuit without calling the model at all.
            redis = Redis.from_url(REDIS_URL)
            killswitch = KillSwitch(redis)

            class _ShouldNotBeCalled:
                async def reasoning(self, messages, **kwargs):  # type: ignore[no-untyped-def]
                    raise AssertionError("model must not be called while agent is paused")

                async def utility(self, messages, **kwargs):  # type: ignore[no-untyped-def]
                    raise AssertionError("model must not be called while agent is paused")

            spec = AgentSpec(name=name, system_prompt="test")
            graph = build_graph(
                spec, llm_client=_ShouldNotBeCalled(), checkpointer=InMemorySaver(),
                killswitch=killswitch,
            )
            result = await graph.ainvoke(
                {"messages": [{"role": "user", "content": "hi"}]},
                {"configurable": {"thread_id": f"live-{uuid.uuid4()}"}},
            )
            assert result["paused"] is True

            resumed = await client.post(f"/v1/admin/agents/{agent_id}/resume")
            assert resumed.status_code == 204

            await client.delete(f"/v1/admin/agents/{agent_id}")
            await redis.aclose()

    import asyncio

    asyncio.run(_run())

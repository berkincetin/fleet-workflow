"""GET /v1/dev-agent/tickets (task 6.5.3): fixture ticket picker for the
Examples gallery's dev_agent try-it dialog. Sourced straight from
DEMO_FIXTURE_TICKETS so the picker never drifts from what a real run
resolves against — this test only proves the route's RBAC gate and response
shape, not the fixture data itself (already covered by test_mcp_jira.py).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.routers import dev_agent as dev_agent_router


def _build_app(*, user: CurrentUser) -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(dev_agent_router.router)

    async def fake_current_user() -> CurrentUser:
        return user

    app.dependency_overrides[get_current_user] = fake_current_user
    return app


def test_member_cannot_list_tickets() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/dev-agent/tickets")
    assert resp.status_code == 403


def test_builder_lists_fixture_tickets() -> None:
    from fleet_mcp.servers.jira import DEMO_FIXTURE_TICKETS

    app = _build_app(user=CurrentUser(sub="u1", roles={"builder"}))
    client = TestClient(app)

    resp = client.get("/v1/dev-agent/tickets")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == len(DEMO_FIXTURE_TICKETS)
    keys = {t["key"] for t in body}
    assert keys == set(DEMO_FIXTURE_TICKETS.keys())
    assert all({"key", "summary", "labels"} <= set(t.keys()) for t in body)

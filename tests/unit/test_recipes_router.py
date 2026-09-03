"""fleet_api.routers.recipes: RBAC + the compile/preview contract (task 13.4).

Only `/v1/recipes/preview` is exercised here because it is the one endpoint
that touches neither Postgres nor n8n — the CRUD + deploy path needs both and
is covered by tests/integration/test_recipes_live.py. What this file pins is
the gate (MANAGE_AGENTS, i.e. a `member` cannot define an automation) and that
an invalid or unsafe recipe is refused with a 422 rather than reaching the
compiler's output.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.routers import recipes as recipes_router


def _client(*roles: str) -> TestClient:
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(recipes_router.router)

    async def fake_current_user() -> CurrentUser:
        return CurrentUser(sub="u-1", roles=set(roles))

    app.dependency_overrides[get_current_user] = fake_current_user
    return TestClient(app)


_VALID = {
    "name": "weekly-check",
    "description": "check sales",
    "trigger": {"type": "schedule", "cron": "0 9 * * 1"},
    "steps": [
        {
            "type": "action",
            "id": "q1",
            "action": "pg.query",
            "params": {"sql": "SELECT COUNT(*) AS n FROM fixture_sales"},
        },
        {
            "type": "condition",
            "id": "c1",
            "left": "{{steps.q1.row_count}}",
            "operator": "gt",
            "right": "0",
            "then_steps": [
                {
                    "type": "action",
                    "id": "e1",
                    "action": "email.send",
                    "params": {"to": "ops@fleet.local", "subject": "Sales", "body": "See report"},
                }
            ],
            "else_steps": [
                {
                    "type": "action",
                    "id": "n1",
                    "action": "http.notify",
                    "params": {"title": "No sales", "message": "nothing to report"},
                }
            ],
        },
    ],
}


def test_member_cannot_preview_a_recipe() -> None:
    resp = _client("member").post("/v1/recipes/preview", json=_VALID)
    assert resp.status_code == 403


def test_builder_can_preview_a_recipe() -> None:
    resp = _client("builder").post("/v1/recipes/preview", json=_VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_write_external"] is True
    assert body["summary"][0] == {"kind": "trigger", "trigger": "schedule", "cron": "0 9 * * 1"}
    assert body["workflow"]["name"] == "fleet-recipe-weekly-check"


def test_preview_rejects_an_unsafe_recipe_with_422() -> None:
    payload = {
        **_VALID,
        "steps": [
            {
                "type": "action",
                "id": "n1",
                "action": "http.notify",
                "params": {"title": "t", "message": "={{ $env.OPENAI_API_KEY }}"},
            }
        ],
    }
    resp = _client("builder").post("/v1/recipes/preview", json=payload)
    assert resp.status_code == 422
    assert "invalid recipe" in resp.json()["detail"]


def test_preview_rejects_an_unknown_action_with_422() -> None:
    payload = {
        **_VALID,
        "steps": [
            {
                "type": "action",
                "id": "x1",
                "action": "http.request",
                "params": {"url": "http://attacker.example"},
            }
        ],
    }
    assert _client("builder").post("/v1/recipes/preview", json=payload).status_code == 422

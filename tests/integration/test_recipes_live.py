"""Integration: recipe -> n8n deploy -> trigger -> Fleet (task 13.4/13.6 AC).

Unlike most `*_live.py` tests here this one cannot run the API in-process: the
compiled workflow is executed *by n8n*, which calls back into Fleet over
`http://host.docker.internal:8000`. So the whole chain is exercised against the
running server (`make api`) and the running stack (`make dev`), which is the
only arrangement that proves the AC — "a schedule-triggered recipe defined
through the API exists and fires in n8n" is not something a mock can answer.

Covers:
  * create -> the recipe is stored in Fleet *and* deployed to n8n
  * activate + run -> n8n really executes it
  * the `email.send` branch produces an approval-queue entry instead of sending
  * delete -> the n8n workflow goes with it
"""

from __future__ import annotations

import os
import time
import uuid

import httpx
import pytest

KEYCLOAK_BASE = "http://localhost:8080"
API_BASE = os.environ.get("FLEET_API_BASE_URL", "http://localhost:8000")
N8N_BASE = "http://localhost:5678"
N8N_API_KEY = os.environ.get("FLEET_N8N_API_KEY", "")


def _api_has_recipes() -> bool:
    try:
        resp = httpx.get(f"{API_BASE}/openapi.json", timeout=5)
        return "/v1/recipes" in resp.json().get("paths", {})
    except Exception:
        return False


def _n8n_up() -> bool:
    try:
        return httpx.get(f"{N8N_BASE}/healthz", timeout=3).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_api_has_recipes() and _n8n_up() and N8N_API_KEY),
    reason=(
        "needs the running stack (`make dev`), a Fleet API serving /v1/recipes "
        "(`make api`, restarted after task 13.4), and FLEET_N8N_API_KEY in the "
        "environment"
    ),
)


def _token(username: str, password: str) -> str:
    resp = httpx.post(
        f"{KEYCLOAK_BASE}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "client_secret": "fleet-api-dev-secret",
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


def _n8n(method: str, path: str, **kwargs: object) -> httpx.Response:
    return httpx.request(
        method,
        f"{N8N_BASE}{path}",
        headers={"X-N8N-API-KEY": N8N_API_KEY},
        timeout=15,
        **kwargs,  # type: ignore[arg-type]
    )


def _executions(workflow_id: str, *, status: str) -> list[dict]:
    resp = _n8n(
        "GET", "/api/v1/executions", params={"workflowId": workflow_id, "status": status}
    )
    return list(resp.json().get("data", [])) if resp.status_code == 200 else []


def _recipe_payload(name: str) -> dict:
    """pg.query -> if row_count > 0 -> email.send, else http.notify.

    Both branches write: one leaves the company (and must be gated), one does
    not — which is what makes this recipe the AC's "a recipe whose branches
    both write is still gated" case as well.
    """
    return {
        "name": name,
        "description": "sprint 13 integration recipe",
        "trigger": {"type": "schedule", "cron": "0 4 * * *"},
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
                        "params": {
                            "to": "ops@fleet.local",
                            "subject": "Sales report",
                            "body": "rows: {{steps.q1.row_count}}",
                        },
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


def _pending_approvals(token: str) -> list[dict]:
    resp = httpx.get(
        f"{API_BASE}/v1/approvals",
        params={"status": "pending"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return list(resp.json())


def test_recipe_deploys_to_n8n_fires_and_gates_its_external_write() -> None:
    builder = _token("builder", "builder")
    approver = _token("approver", "approver")
    headers = {"Authorization": f"Bearer {builder}"}
    name = f"itest-{uuid.uuid4().hex[:8]}"

    created = httpx.post(
        f"{API_BASE}/v1/recipes", json=_recipe_payload(name), headers=headers, timeout=30
    )
    assert created.status_code == 201, created.text
    recipe = created.json()
    recipe_id = recipe["id"]

    try:
        # --- deployed to n8n, not just stored in Fleet
        assert recipe["deploy_error"] is None, recipe["deploy_error"]
        assert recipe["n8n_workflow_id"], "recipe was not deployed to n8n"
        assert recipe["has_write_external"] is True

        in_n8n = _n8n("GET", f"/api/v1/workflows/{recipe['n8n_workflow_id']}")
        assert in_n8n.status_code == 200, in_n8n.text
        workflow = in_n8n.json()
        assert workflow["name"] == f"fleet-recipe-{name}"
        node_types = {node["type"] for node in workflow["nodes"]}
        assert "n8n-nodes-base.code" not in node_types
        assert "n8n-nodes-base.scheduleTrigger" in node_types
        assert "n8n-nodes-base.if" in node_types

        # --- activate, then trigger it now rather than waiting for the cron
        activated = httpx.post(
            f"{API_BASE}/v1/recipes/{recipe_id}/activate", headers=headers, timeout=30
        )
        assert activated.status_code == 200, activated.text
        assert activated.json()["status"] == "ok"

        approvals_before = len(_pending_approvals(approver))

        ran = httpx.post(f"{API_BASE}/v1/recipes/{recipe_id}/run", headers=headers, timeout=30)
        assert ran.status_code == 202, ran.text
        assert ran.json()["status"] == "ok", ran.text

        # --- n8n really executed it.
        # n8n 1.71's public executions list omits the `status` field on each
        # row, so success/failure is read from the server-side filter rather
        # than the row body.
        deadline = time.time() + 60
        succeeded: list[dict] = []
        failed: list[dict] = []
        while time.time() < deadline:
            succeeded = _executions(recipe["n8n_workflow_id"], status="success")
            failed = _executions(recipe["n8n_workflow_id"], status="error")
            if succeeded or failed:
                break
            time.sleep(2)
        assert not failed, f"the recipe's n8n execution failed: {failed}"
        assert succeeded, "n8n recorded no execution for the recipe"
        assert succeeded[0]["finished"] is True

        # --- the write:external step queued an approval instead of sending
        deadline = time.time() + 20
        queued: list[dict] = []
        while time.time() < deadline:
            queued = [a for a in _pending_approvals(approver) if a["action"] == "email.send"]
            if len(_pending_approvals(approver)) > approvals_before:
                break
            time.sleep(1)
        assert queued, "email.send did not produce an approval-queue entry"
        latest = queued[-1]
        assert latest["payload"]["to"] == "ops@fleet.local"
        assert latest["status"] == "pending"

    finally:
        deleted = httpx.delete(
            f"{API_BASE}/v1/recipes/{recipe_id}", headers=headers, timeout=30
        )
        assert deleted.status_code == 200, deleted.text

    # --- deleting the recipe removes its workflow from n8n too
    gone = _n8n("GET", f"/api/v1/workflows/{recipe['n8n_workflow_id']}")
    assert gone.status_code == 404, gone.text


def test_member_cannot_create_a_recipe_but_can_list_them() -> None:
    member = {"Authorization": f"Bearer {_token('user1', 'user1')}"}
    refused = httpx.post(
        f"{API_BASE}/v1/recipes",
        json=_recipe_payload("itest-forbidden"),
        headers=member,
        timeout=15,
    )
    assert refused.status_code == 403
    assert httpx.get(f"{API_BASE}/v1/recipes", headers=member, timeout=15).status_code == 200


def test_a_crafted_recipe_is_refused_before_it_reaches_n8n() -> None:
    headers = {"Authorization": f"Bearer {_token('builder', 'builder')}"}
    payload = _recipe_payload("itest-crafted")
    payload["steps"] = [
        {
            "type": "action",
            "id": "n1",
            "action": "http.notify",
            "params": {"title": "t", "message": "={{ $env.LITELLM_MASTER_KEY }}"},
        }
    ]
    resp = httpx.post(f"{API_BASE}/v1/recipes", json=payload, headers=headers, timeout=15)
    assert resp.status_code == 422
    listing = _n8n("GET", "/api/v1/workflows")
    names = {w["name"] for w in listing.json().get("data", [])}
    assert "fleet-recipe-itest-crafted" not in names

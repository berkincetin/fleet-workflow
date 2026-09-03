"""fleet_api.routers.workflows: friendly n8n catalog + run/activate proxy
(task 6.5.3). N8nClient is dependency-overridden with a fake that returns
canned N8nResult values — no real n8n or Postgres needed. Covers: catalog
merge shape, the "n8n down -> 200 with reachable:false" contract, RBAC gates,
and upload validation on the invoice-intake run endpoint.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.n8n_client import N8nResult
from fleet_api.routers import workflows as workflows_router
from fleet_api.workflows_catalog import CATALOG


class _FakeN8nClient:
    def __init__(
        self,
        *,
        list_result: N8nResult | None = None,
        executions_result: N8nResult | None = None,
        action_result: N8nResult | None = None,
    ) -> None:
        self.list_result = list_result or N8nResult(reachable=False)
        self.executions_result = executions_result or N8nResult(reachable=True, data={"data": []})
        self.action_result = action_result or N8nResult(reachable=True, data={"ok": True})
        self.calls: list[tuple[str, tuple, dict]] = []

    async def list_workflows(self) -> N8nResult:
        self.calls.append(("list_workflows", (), {}))
        return self.list_result

    async def list_executions(self, workflow_id: str, *, limit: int = 1) -> N8nResult:
        self.calls.append(("list_executions", (workflow_id,), {"limit": limit}))
        return self.executions_result

    async def set_active(self, workflow_id: str, active: bool) -> N8nResult:
        self.calls.append(("set_active", (workflow_id, active), {}))
        return self.action_result

    async def trigger_webhook_json(self, path: str, body: dict) -> N8nResult:
        self.calls.append(("trigger_webhook_json", (path, body), {}))
        return self.action_result


def _build_app(*, n8n_client: _FakeN8nClient, user: CurrentUser) -> FastAPI:
    """Overrides get_current_user (not require_permission's per-call-site
    closures — see test_examples_router.py for why those don't share
    identity) so the router's real require_permission(...) dependencies run
    their actual CHAT/UPLOAD/MANAGE_AGENTS checks against the fake user."""
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(workflows_router.router)

    async def fake_current_user() -> CurrentUser:
        return user

    app.dependency_overrides[workflows_router.get_n8n_client] = lambda: n8n_client
    app.dependency_overrides[get_current_user] = fake_current_user
    return app


def test_catalog_returns_200_with_reachable_false_when_n8n_down() -> None:
    fake = _FakeN8nClient(list_result=N8nResult(reachable=False, error="connect failed"))
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/workflows")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert all(w["reachable"] is False for w in body)


def test_catalog_merges_live_n8n_state() -> None:
    fake = _FakeN8nClient(
        list_result=N8nResult(
            reachable=True,
            data={"data": [{"id": "1", "name": "invoice-intake", "active": True}]},
        ),
        executions_result=N8nResult(
            reachable=True, data={"data": [{"status": "success", "startedAt": "2026-07-20"}]}
        ),
    )
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/workflows")
    assert resp.status_code == 200
    body = resp.json()
    invoice = next(w for w in body if w["slug"] == "invoice-intake")
    assert invoice["active"] is True
    assert invoice["last_run"]["status"] == "success"
    weekly = next(w for w in body if w["slug"] == "weekly-summary")
    assert weekly["active"] is None  # not found in n8n's list -> unknown, not False


def test_member_cannot_activate_workflow() -> None:
    fake = _FakeN8nClient()
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post("/v1/workflows/invoice-intake/activate")
    assert resp.status_code == 403


def test_builder_can_activate_workflow() -> None:
    fake = _FakeN8nClient(
        list_result=N8nResult(
            reachable=True, data={"data": [{"id": "1", "name": "invoice-intake", "active": False}]}
        ),
    )
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"builder"}))
    client = TestClient(app)

    resp = client.post("/v1/workflows/invoice-intake/activate")
    assert resp.status_code == 200
    assert ("set_active", ("1", True), {}) in fake.calls


def test_invoice_run_rejects_unsupported_content_type() -> None:
    fake = _FakeN8nClient()
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/workflows/invoice-intake/run",
        files={"file": ("invoice.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert resp.status_code == 422


def test_invoice_run_reports_workflow_inactive() -> None:
    fake = _FakeN8nClient(
        list_result=N8nResult(
            reachable=True, data={"data": [{"id": "1", "name": "invoice-intake", "active": False}]}
        ),
    )
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/workflows/invoice-intake/run",
        files={"file": ("invoice.png", io.BytesIO(b"\x89PNG\r\n"), "image/png")},
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "workflow_inactive"


def test_invoice_run_accepts_when_active_and_reachable() -> None:
    fake = _FakeN8nClient(
        list_result=N8nResult(
            reachable=True, data={"data": [{"id": "1", "name": "invoice-intake", "active": True}]}
        ),
    )
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/workflows/invoice-intake/run",
        files={"file": ("invoice.png", io.BytesIO(b"\x89PNG\r\n"), "image/png")},
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"
    assert any(call[0] == "trigger_webhook_json" for call in fake.calls)


def test_weekly_summary_run_requires_manage_agents() -> None:
    fake = _FakeN8nClient()
    app = _build_app(n8n_client=fake, user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.post("/v1/workflows/weekly-summary/run")
    assert resp.status_code == 403


def test_catalog_names_match_the_workflow_exports() -> None:
    """`n8n_name` is compared verbatim against n8n's workflow list, so a drift
    between the catalog and `workflows/*.json` makes a workflow invisible to the
    UI (`active: null`) while it is imported and active in n8n. That is exactly
    what shipped in 6.5.3 — the catalog said "Weekly summary", the export says
    "weekly-summary" — and it was invisible to the suite because every other
    test builds its own fixture instead of reading the real exports."""
    root = Path(__file__).resolve().parents[2]
    exported = {
        json.loads(p.read_text(encoding="utf-8"))["name"]
        for p in (root / "workflows").glob("*.json")
    }
    for meta in CATALOG.values():
        assert meta.n8n_name in exported, (
            f"catalog entry {meta.slug!r} points at n8n_name {meta.n8n_name!r}, "
            f"which no export in workflows/ declares (found: {sorted(exported)})"
        )


def test_workflow_exports_declare_active() -> None:
    """n8n's importer writes `active` into a NOT NULL column and imports a
    directory all-or-nothing, so one export missing the key blocks every other
    workflow too (`make n8n-import` fails with a constraint violation)."""
    root = Path(__file__).resolve().parents[2]
    for p in sorted((root / "workflows").glob("*.json")):
        assert "active" in json.loads(p.read_text(encoding="utf-8")), (
            f"{p.name} has no top-level 'active' key — n8n import will fail"
        )


def test_a_finished_execution_without_a_status_field_reports_success() -> None:
    """n8n 1.71's executions list carries `finished` but no `status`; reporting
    the missing field verbatim rendered every completed run as a red badge on
    the Home dashboard (task 13.1)."""
    from fleet_api.routers.workflows import _execution_status

    assert _execution_status({"finished": True}) == "success"
    # Stopped but not finished is a run that died at a node, not one in flight.
    assert _execution_status({"finished": False, "stoppedAt": "2026-09-03T03:36:26Z"}) == "error"
    assert _execution_status({"finished": False}) == "running"
    # An explicit status always wins.
    assert _execution_status({"finished": True, "status": "error"}) == "error"

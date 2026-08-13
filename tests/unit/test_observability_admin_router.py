"""fleet_api.routers.observability_admin: cost dashboard + audit explorer
(task 7.2). Only the RBAC gate and query-param validation that runs before
any DB access is unit-tested here; the real aggregation queries and the
Langfuse deep-link builder are covered by
tests/integration/test_observability_admin_router_live.py.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.routers import observability_admin as observability_admin_router


class _UntouchedSession:
    async def execute(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("session.execute should not have been called")


def _build_app(*, user: CurrentUser) -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(observability_admin_router.router)

    async def fake_current_user() -> CurrentUser:
        return user

    async def fake_get_session():  # type: ignore[no-untyped-def]
        yield _UntouchedSession()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[observability_admin_router.get_session] = fake_get_session
    return app


def test_member_cannot_view_cost_summary() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/admin/cost/summary")
    assert resp.status_code == 403


def test_member_cannot_view_audit() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/admin/audit")
    assert resp.status_code == 403


def test_cost_summary_rejects_out_of_range_days_before_touching_db() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"platform_admin"}))
    client = TestClient(app)

    resp = client.get("/v1/admin/cost/summary", params={"days": 0})
    assert resp.status_code == 422


def test_audit_rejects_out_of_range_limit_before_touching_db() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"platform_admin"}))
    client = TestClient(app)

    resp = client.get("/v1/admin/audit", params={"limit": 0})
    assert resp.status_code == 422

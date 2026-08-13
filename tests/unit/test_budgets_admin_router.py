"""fleet_api.routers.budgets_admin: budgets CRUD (task 7.1b, TRD §5). Only the
RBAC gate and request-validation logic that runs before any DB access is
unit-tested here (no fake-session emulation); the real DB round trip and
uniqueness constraint are covered by tests/integration/test_budgets_admin_router_live.py.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.routers import budgets_admin as budgets_admin_router


class _UntouchedSession:
    async def execute(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("session.execute should not have been called")

    async def get(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("session.get should not have been called")


def _build_app(*, user: CurrentUser) -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(budgets_admin_router.router)

    async def fake_current_user() -> CurrentUser:
        return user

    async def fake_get_session():  # type: ignore[no-untyped-def]
        yield _UntouchedSession()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[budgets_admin_router.get_session] = fake_get_session
    return app


def test_member_cannot_list_budgets() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/admin/budgets")
    assert resp.status_code == 403


def test_unknown_scope_type_rejected_before_touching_db() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"platform_admin"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/admin/budgets",
        json={"scope_type": "planet", "scope_id": None, "limit_usd": 100.0},
    )
    assert resp.status_code == 422


def test_global_scope_with_scope_id_rejected_before_touching_db() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"platform_admin"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/admin/budgets",
        json={"scope_type": "global", "scope_id": "1", "limit_usd": 100.0},
    )
    assert resp.status_code == 422


def test_non_global_scope_without_scope_id_rejected_before_touching_db() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"platform_admin"}))
    client = TestClient(app)

    resp = client.post(
        "/v1/admin/budgets",
        json={"scope_type": "dept", "scope_id": None, "limit_usd": 100.0},
    )
    assert resp.status_code == 422

"""fleet_api.routers.users_admin: users/roles admin CRUD (task 7.1). Only the
RBAC gate and request-validation logic that runs before any DB access is
unit-tested here (no fake-session join emulation); the real multi-table
listing/role-edit round trip against Postgres is covered by
tests/integration/test_users_admin_router_live.py.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.routers import users_admin as users_admin_router


class _UntouchedSession:
    """Raises if the router ever tries to use it — proves a code path never
    reaches the DB (e.g. request validation short-circuits first)."""

    async def execute(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("session.execute should not have been called")

    async def get(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("session.get should not have been called")


def _build_app(*, user: CurrentUser) -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(users_admin_router.router)

    async def fake_current_user() -> CurrentUser:
        return user

    async def fake_get_session():  # type: ignore[no-untyped-def]
        yield _UntouchedSession()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[users_admin_router.get_session] = fake_get_session
    return app


def test_member_cannot_list_users() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"member"}))
    client = TestClient(app)

    resp = client.get("/v1/admin/users")
    assert resp.status_code == 403


def test_dept_admin_cannot_list_users() -> None:
    # 7.1 keeps user/role management platform_admin-only, same tier as
    # models/API-keys admin — dept_admin gets manage_dept, not manage_platform.
    app = _build_app(user=CurrentUser(sub="u1", roles={"dept_admin"}))
    client = TestClient(app)

    resp = client.get("/v1/admin/users")
    assert resp.status_code == 403


def test_unknown_role_name_rejected_before_touching_db() -> None:
    app = _build_app(user=CurrentUser(sub="u1", roles={"platform_admin"}))
    client = TestClient(app)

    resp = client.post("/v1/admin/users/1/roles", json={"role": "superuser"})
    assert resp.status_code == 422

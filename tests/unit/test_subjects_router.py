"""fleet_api.routers.subjects: right-to-erasure endpoint (task 8.3, TRD §8).
Only the RBAC gate that runs before any DB access is unit-tested here; the
real erasure (conversations/documents deletion + audit pseudonymization) is
covered by tests/integration/test_subjects_router_live.py.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.routers import subjects as subjects_router


class _UntouchedSession:
    async def execute(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("session.execute should not have been called")

    async def get(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("session.get should not have been called")


def _build_app(*, user: CurrentUser) -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(subjects_router.router)

    async def fake_current_user() -> CurrentUser:
        return user

    async def fake_get_session():  # type: ignore[no-untyped-def]
        yield _UntouchedSession()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[subjects_router.get_session] = fake_get_session
    return app


def test_member_cannot_erase_a_subject() -> None:
    app = _build_app(user=CurrentUser(sub="user1", roles={"member"}))
    client = TestClient(app)
    resp = client.delete("/v1/subjects/deadbeef")
    assert resp.status_code == 403


def test_dept_admin_cannot_erase_a_subject() -> None:
    """Erasure is a platform-tier action (same gate as users_admin/budgets_admin),
    not dept-scoped — a dept_admin does not automatically get it."""
    app = _build_app(user=CurrentUser(sub="deptadmin", roles={"dept_admin"}))
    client = TestClient(app)
    resp = client.delete("/v1/subjects/deadbeef")
    assert resp.status_code == 403

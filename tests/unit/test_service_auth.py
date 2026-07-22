"""fleet_api.service_auth: X-Fleet-Api-Key auth + require_user_or_service_scope
(task 6.1/6.3). The dual-auth dependency lets a route (invoice-agent's run
trigger, 6.3) be reachable by EITHER a Keycloak bearer token with a given
Permission OR a Fleet API key with a given scope — n8n has no Keycloak
session, so this is what lets its webhook intake path call the same route a
human/future admin UI would use directly.

A minimal FastAPI app with the DB session and OIDC verification faked out
(no real Postgres/Keycloak needed) proves the routing/priority/error-shape
logic; the real end-to-end auth (real hash lookup, real JWKS validation) is
proven in tests/integration/test_api_keys_live.py and the live invoice-agent
e2e test.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from fleet_api.api_keys import hash_key
from fleet_api.auth import CurrentUser
from fleet_api.config import Settings
from fleet_api.rbac import Permission
from fleet_api.service_auth import require_user_or_service_scope


class _FakeResult:
    def __init__(self, row: Any) -> None:
        self._row = row

    def scalar_one_or_none(self) -> Any:
        return self._row


class _FakeApiKeyRow:
    def __init__(self, *, hash_: str, scopes: list[str], revoked: bool = False) -> None:
        self.id = 1
        self.name = "test-key"
        self.hash = hash_
        self.scopes = scopes
        self.expires_at: dt.datetime | None = None
        self.revoked_at: dt.datetime | None = dt.datetime.now(dt.UTC) if revoked else None


class _FakeSession:
    def __init__(self, row: Any) -> None:
        self._row = row

    async def execute(self, *args: object, **kwargs: object) -> _FakeResult:
        return _FakeResult(self._row)


def _build_app(*, db_row: Any, verified_user: CurrentUser | None) -> FastAPI:
    from fleet_api import service_auth as sa_module
    from fleet_api.errors import install_error_handlers

    app = FastAPI()
    install_error_handlers(app)

    async def fake_get_session():  # type: ignore[no-untyped-def]
        yield _FakeSession(db_row)

    async def fake_verify_bearer_token(token: str, settings: Settings) -> CurrentUser:
        if verified_user is None:
            from fleet_api.errors import UnauthorizedError

            raise UnauthorizedError("invalid token")
        return verified_user

    # Patch the module-level symbol require_user_or_service_scope's closure
    # calls — verify_bearer_token is imported by name into service_auth, so
    # patch it there (not in fleet_api.auth) for the closure to see the fake.
    sa_module.verify_bearer_token = fake_verify_bearer_token  # type: ignore[assignment]

    @app.get("/protected")
    async def protected(
        principal: object = Depends(  # noqa: B008
            require_user_or_service_scope(Permission.MANAGE_AGENTS, "invoice_intake")
        ),
    ) -> dict[str, str]:
        return {"ok": "true"}

    app.dependency_overrides[sa_module.get_session] = fake_get_session
    return app


@pytest.fixture(autouse=True)
def _restore_verify_bearer_token():  # type: ignore[no-untyped-def]
    from fleet_api import auth as auth_module
    from fleet_api import service_auth as sa_module

    original = auth_module.verify_bearer_token
    yield
    sa_module.verify_bearer_token = original


def test_no_credentials_at_all_returns_401() -> None:
    app = _build_app(db_row=None, verified_user=None)
    client = TestClient(app)
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_valid_bearer_token_with_permission_is_allowed() -> None:
    user = CurrentUser(sub="builder-1", roles={"builder"})
    app = _build_app(db_row=None, verified_user=user)
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer faketoken"})
    assert resp.status_code == 200


def test_valid_bearer_token_without_permission_returns_403() -> None:
    user = CurrentUser(sub="member-1", roles={"member"})  # no MANAGE_AGENTS
    app = _build_app(db_row=None, verified_user=user)
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer faketoken"})
    assert resp.status_code == 403


def test_valid_service_key_with_scope_is_allowed() -> None:
    raw_key = "fk_test_key"
    row = _FakeApiKeyRow(hash_=hash_key(raw_key), scopes=["invoice_intake"])
    app = _build_app(db_row=row, verified_user=None)
    client = TestClient(app)
    resp = client.get("/protected", headers={"X-Fleet-Api-Key": raw_key})
    assert resp.status_code == 200


def test_service_key_missing_scope_returns_403() -> None:
    raw_key = "fk_test_key"
    row = _FakeApiKeyRow(hash_=hash_key(raw_key), scopes=["pg_ro"])
    app = _build_app(db_row=row, verified_user=None)
    client = TestClient(app)
    resp = client.get("/protected", headers={"X-Fleet-Api-Key": raw_key})
    assert resp.status_code == 403


def test_revoked_service_key_returns_401() -> None:
    raw_key = "fk_test_key"
    row = _FakeApiKeyRow(hash_=hash_key(raw_key), scopes=["invoice_intake"], revoked=True)
    app = _build_app(db_row=row, verified_user=None)
    client = TestClient(app)
    resp = client.get("/protected", headers={"X-Fleet-Api-Key": raw_key})
    assert resp.status_code == 401


def test_unknown_service_key_returns_401() -> None:
    app = _build_app(db_row=None, verified_user=None)
    client = TestClient(app)
    resp = client.get("/protected", headers={"X-Fleet-Api-Key": "fk_unknown"})
    assert resp.status_code == 401


def test_bearer_token_is_tried_before_service_key_when_both_present() -> None:
    """Both credentials present: the bearer token path wins, per
    require_user_or_service_scope's documented priority — proven by a bearer
    token that fails permission (403) even though a valid service key with
    the right scope is also on the request."""
    user = CurrentUser(sub="member-1", roles={"member"})
    raw_key = "fk_test_key"
    row = _FakeApiKeyRow(hash_=hash_key(raw_key), scopes=["invoice_intake"])
    app = _build_app(db_row=row, verified_user=user)
    client = TestClient(app)
    resp = client.get(
        "/protected",
        headers={"Authorization": "Bearer faketoken", "X-Fleet-Api-Key": raw_key},
    )
    assert resp.status_code == 403

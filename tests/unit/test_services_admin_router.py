"""fleet_api.routers.services_admin: RBAC + the credential-masking contract
(task 13.3).

The AC this file exists for: **credential values must be absent from the API
response body for a non-`platform_admin` caller.** That is asserted twice —
once on the 403 a non-admin gets from the list endpoint, and once on the
reveal endpoint, which additionally refuses a caller who holds MANAGE_PLATFORM
but not the `platform_admin` role.

The probes themselves are not exercised here (they need the live stack); the
list endpoint's happy path is covered by
tests/integration/test_services_admin_live.py.
"""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fleet_api.auth import CurrentUser, get_current_user
from fleet_api.errors import install_error_handlers
from fleet_api.rbac import ROLE_PERMISSIONS, Permission
from fleet_api.routers import services_admin
from fleet_api.services_catalog import CATALOG, CATALOG_BY_NAME, mask_secret

SECRET = "super-secret-dev-password"


def _client(*roles: str) -> TestClient:
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(services_admin.router)

    async def fake_current_user() -> CurrentUser:
        return CurrentUser(sub="u-1", roles=set(roles))

    app.dependency_overrides[get_current_user] = fake_current_user
    return TestClient(app)


@pytest.fixture()
def keycloak_secret_in_env() -> object:
    previous = os.environ.get("KEYCLOAK_ADMIN_PASSWORD")
    os.environ["KEYCLOAK_ADMIN_PASSWORD"] = SECRET
    yield
    if previous is None:
        os.environ.pop("KEYCLOAK_ADMIN_PASSWORD", None)
    else:
        os.environ["KEYCLOAK_ADMIN_PASSWORD"] = previous


@pytest.mark.parametrize("role", ["member", "builder", "approver", "dept_admin"])
def test_non_platform_admin_roles_get_403_and_no_credential_in_the_body(
    role: str, keycloak_secret_in_env: object
) -> None:
    resp = _client(role).get("/v1/admin/services")
    assert resp.status_code == 403
    assert SECRET not in resp.text


@pytest.mark.parametrize("role", ["member", "builder", "approver", "dept_admin"])
def test_non_platform_admin_roles_cannot_reveal(
    role: str, keycloak_secret_in_env: object
) -> None:
    resp = _client(role).post("/v1/admin/services/keycloak/reveal")
    assert resp.status_code == 403
    assert SECRET not in resp.text


def test_reveal_refuses_manage_platform_without_the_platform_admin_role(
    keycloak_secret_in_env: object,
) -> None:
    """MANAGE_PLATFORM is currently held only by `platform_admin`, but the
    reveal endpoint does not rely on that staying true — it checks the role
    itself, so widening the permission later cannot silently widen who can
    read a plaintext credential."""
    assert Permission.MANAGE_PLATFORM in ROLE_PERMISSIONS["platform_admin"]

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(services_admin.router)

    async def fake_current_user() -> CurrentUser:
        return CurrentUser(sub="u-1", roles={"future_ops_role"})

    app.dependency_overrides[get_current_user] = fake_current_user
    # Grant the permission without the role, exactly the drift being guarded.
    ROLE_PERMISSIONS["future_ops_role"] = {Permission.MANAGE_PLATFORM}
    try:
        resp = TestClient(app).post("/v1/admin/services/keycloak/reveal")
    finally:
        del ROLE_PERMISSIONS["future_ops_role"]

    assert resp.status_code == 403
    assert SECRET not in resp.text


def test_platform_admin_reveal_returns_the_plaintext(keycloak_secret_in_env: object) -> None:
    resp = _client("platform_admin").post("/v1/admin/services/keycloak/reveal")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "keycloak"
    assert body["credentials"][0]["secret"] == SECRET


def test_reveal_404s_on_an_unknown_service() -> None:
    assert _client("platform_admin").post("/v1/admin/services/nope/reveal").status_code == 404


def test_mask_secret_never_returns_a_usable_value() -> None:
    assert mask_secret(SECRET) == "su••••••rd"
    # Short secrets are masked whole — showing 2 of 6 characters is a real
    # fraction of the search space.
    assert mask_secret("admin") == "•" * 8
    assert mask_secret(None) is None


def test_catalog_stores_variable_names_not_values() -> None:
    """Nothing in the catalog module is a committed secret."""
    for spec in CATALOG:
        for cred in spec.credentials:
            assert cred.secret_env.isupper()
    # The compose defaults that are documented in the repo already are allowed
    # as fallbacks, but only those.
    assert CATALOG_BY_NAME["postgres"].credentials[0].default_secret == "fleet_dev_pw"

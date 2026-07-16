"""Integration test: 401 without/with a bad token, 200 with a valid member token,
403 when the token lacks the required permission — against a real Keycloak."""

from __future__ import annotations

import time

import httpx
import pytest
from fastapi.testclient import TestClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

REALM = {
    "realm": "fleet",
    "enabled": True,
    "sslRequired": "none",
    "requiredCredentials": ["password"],
    "passwordPolicy": "length(8)",
    "clients": [
        {
            "clientId": "fleet-api",
            "enabled": True,
            "publicClient": True,
            "directAccessGrantsEnabled": True,
            "standardFlowEnabled": True,
            "redirectUris": ["*"],
        }
    ],
    "roles": {"realm": [{"name": "member"}, {"name": "builder"}]},
    "users": [
        {
            "username": "m",
            "enabled": True,
            "email": "m@fleet.test",
            "emailVerified": True,
            "firstName": "Test",
            "lastName": "User",
            "credentials": [{"type": "password", "value": "password123", "temporary": False}],
            "realmRoles": ["member"],
        }
    ],
}


@pytest.fixture(scope="module")
def keycloak() -> str:
    import json
    import tempfile

    container = (
        DockerContainer("quay.io/keycloak/keycloak:26.0")
        .with_command("start-dev --import-realm")
        .with_env("KC_BOOTSTRAP_ADMIN_USERNAME", "admin")
        .with_env("KC_BOOTSTRAP_ADMIN_PASSWORD", "admin")
        .with_exposed_ports(8080)
    )
    # Write the realm to a temp dir mounted at the import path.
    tmp = tempfile.mkdtemp()
    with open(f"{tmp}/fleet-realm.json", "w", encoding="utf-8") as fh:
        json.dump(REALM, fh)
    container.with_volume_mapping(tmp, "/opt/keycloak/data/import", "ro")
    with container:
        wait_for_logs(container, "Listening on", timeout=120)
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8080)
        base = f"http://{host}:{port}"
        # Give the realm import a moment.
        for _ in range(30):
            try:
                r = httpx.get(f"{base}/realms/fleet/.well-known/openid-configuration", timeout=3)
                if r.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(2)
        yield base


def _token(base: str, username: str, password: str) -> str:
    resp = httpx.post(
        f"{base}/realms/fleet/protocol/openid-connect/token",
        data={
            "client_id": "fleet-api",
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _client(base: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("FLEET_OIDC_ISSUER", f"{base}/realms/fleet")
    monkeypatch.setenv(
        "FLEET_OIDC_JWKS_URL",
        f"{base}/realms/fleet/protocol/openid-connect/certs",
    )
    monkeypatch.setenv("FLEET_OIDC_AUDIENCE", "account")
    from fleet_api.app import create_app

    return TestClient(create_app())


def test_401_without_token(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(keycloak, monkeypatch)
    assert client.get("/whoami").status_code == 401


def test_401_bad_token(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(keycloak, monkeypatch)
    r = client.get("/whoami", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_200_member_has_chat(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    token = _token(keycloak, "m", "password123")
    client = _client(keycloak, monkeypatch)
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "member" in r.json()["roles"]


def test_403_member_lacks_admin(keycloak: str, monkeypatch: pytest.MonkeyPatch) -> None:
    token = _token(keycloak, "m", "password123")
    client = _client(keycloak, monkeypatch)
    r = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

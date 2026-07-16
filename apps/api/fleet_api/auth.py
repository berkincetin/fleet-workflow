"""OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fleet_api.config import Settings, get_settings
from fleet_api.errors import UnauthorizedError
from jose import jwt
from jose.exceptions import JWTError

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """The authenticated principal extracted from a verified token."""

    sub: str
    roles: set[str] = field(default_factory=set)


async def _fetch_jwks(url: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


def _extract_roles(claims: dict) -> set[str]:
    # Keycloak puts realm roles under realm_access.roles.
    realm = claims.get("realm_access", {}) or {}
    return set(realm.get("roles", []))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> CurrentUser:
    """Verify the bearer token and return the current user, or raise 401."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("missing bearer token")
    token = credentials.credentials
    try:
        jwks = await _fetch_jwks(settings.oidc_jwks_url)
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"verify_aud": True},
        )
    except (JWTError, httpx.HTTPError) as exc:
        raise UnauthorizedError("invalid token") from exc
    sub = claims.get("sub")
    if not sub:
        raise UnauthorizedError("token missing sub")
    return CurrentUser(sub=sub, roles=_extract_roles(claims))

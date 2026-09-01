"""OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.errors import UnauthorizedError
from fleet_api.users import get_or_create_user, load_roles, seed_roles_from_jwt
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """The authenticated principal extracted from a verified token."""

    sub: str
    roles: set[str] = field(default_factory=set)
    # Carried only as far as `get_or_create_user`, which stores its hash — the
    # raw address is never persisted or logged (TRD §8).
    email: str | None = None


async def _fetch_jwks(url: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


def _extract_roles(claims: dict) -> set[str]:
    # Keycloak puts realm roles under realm_access.roles.
    realm = claims.get("realm_access", {}) or {}
    return set(realm.get("roles", []))


async def verify_bearer_token(token: str, settings: Settings) -> CurrentUser:
    """Verify a raw bearer token string and return the current user, or raise 401.

    This is the FastAPI-DI-free core of `get_current_user`, so non-request-scoped
    callers (e.g. middleware) can verify a token without going through `Depends`.
    """
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
    return CurrentUser(sub=sub, roles=_extract_roles(claims), email=claims.get("email"))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CurrentUser:
    """Verify the bearer token, then resolve permissions against the DB
    `roles` table rather than the token's own claims (task 7.1). Keycloak
    stays the identity provider; a first login copies its realm roles into
    the DB once (`seed_roles_from_jwt`), and every request after that reads
    live from `roles` — so an admin's role edit takes effect on the caller's
    very next request instead of waiting on token refresh.
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("missing bearer token")
    jwt_user = await verify_bearer_token(credentials.credentials, settings)
    db_user = await get_or_create_user(session, kc_sub=jwt_user.sub, email=jwt_user.email)
    await seed_roles_from_jwt(session, db_user, jwt_user.roles)
    await session.commit()
    db_roles = await load_roles(session, db_user)
    return CurrentUser(sub=jwt_user.sub, roles=db_roles)


async def try_current_user_sub(auth_header: str | None, settings: Settings) -> str | None:
    """Best-effort verified `sub` extraction from a raw Authorization header value.

    Returns None (never raises) when the header is missing, malformed, or the
    token fails verification — callers that only need an audit actor should not
    fail the request over a bad/absent token.
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer ") :]
    try:
        user = await verify_bearer_token(token, settings)
    except UnauthorizedError:
        return None
    return user.sub

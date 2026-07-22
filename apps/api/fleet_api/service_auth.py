"""FastAPI dependency for Fleet-issued API-key auth (task 6.1, TRD §7.1).

Parallel to `auth.py`'s Keycloak-bearer `get_current_user` — this is the
"programmatic access" leg for services (n8n, other automations) that aren't a
logged-in human and don't hold an OIDC session. Callers present a raw key via
the `X-Fleet-Api-Key` header; it's hashed and looked up, never compared
plaintext-to-plaintext.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fleet_api.api_keys import ApiKeyInvalid, ApiKeyRecord, hash_key, validate_record
from fleet_api.auth import CurrentUser, verify_bearer_token
from fleet_api.config import Settings, get_settings
from fleet_api.db import get_session
from fleet_api.errors import ForbiddenError, UnauthorizedError
from fleet_api.models import ApiKey
from fleet_api.rbac import Permission, permissions_for
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_optional_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentServiceKey:
    """The authenticated principal for a Fleet-API-key-authenticated request."""

    id: int
    name: str
    scopes: list[str]


async def _lookup(session: AsyncSession, raw_key: str) -> ApiKeyRecord | None:
    stored_hash = hash_key(raw_key)
    row = (
        await session.execute(select(ApiKey).where(ApiKey.hash == stored_hash))
    ).scalar_one_or_none()
    if row is None:
        return None
    return ApiKeyRecord(
        id=row.id,
        name=row.name,
        scopes=row.scopes,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
    )


async def get_current_service_key(
    x_fleet_api_key: str | None = Header(default=None),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CurrentServiceKey:
    """Validate the `X-Fleet-Api-Key` header, or raise 401."""
    if not x_fleet_api_key:
        raise UnauthorizedError("missing X-Fleet-Api-Key header")
    record = await _lookup(session, x_fleet_api_key)
    try:
        valid = validate_record(record, now=dt.datetime.now(dt.UTC))
    except ApiKeyInvalid as exc:
        raise UnauthorizedError(str(exc)) from exc
    return CurrentServiceKey(id=valid.id, name=valid.name, scopes=valid.scopes)


def require_scope(scope: str):
    """Dependency factory: allow the request only if the key holds `scope`."""

    async def _dep(
        key: CurrentServiceKey = Depends(get_current_service_key),  # noqa: B008
    ) -> CurrentServiceKey:
        if scope not in key.scopes:
            raise ForbiddenError(f"api key missing scope: {scope}")
        return key

    return _dep


def require_user_or_service_scope(permission: Permission, scope: str):
    """Dependency factory: allow the request if EITHER a Keycloak bearer
    token carries `permission` (a logged-in human — e.g. a future admin UI
    triggering a run directly) OR an `X-Fleet-Api-Key` carries `scope` (a
    service — n8n's webhook path, task 6.3). Same "route stays reachable by
    both caller kinds" shape as picking a route prefix wouldn't give without
    duplicating the graph-wiring logic across two endpoints.

    Tries the bearer token first since it's the common human-triggered case;
    falls back to the API key only if no valid bearer token was presented,
    never partially trusting one over the other.
    """

    async def _dep(
        credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),  # noqa: B008
        x_fleet_api_key: str | None = Header(default=None),  # noqa: B008
        settings: Settings = Depends(get_settings),  # noqa: B008
        session: AsyncSession = Depends(get_session),  # noqa: B008
    ) -> CurrentUser | CurrentServiceKey:
        if credentials is not None and credentials.credentials:
            user = await verify_bearer_token(credentials.credentials, settings)
            if permission not in permissions_for(user.roles):
                raise ForbiddenError(f"missing permission: {permission}")
            return user

        if x_fleet_api_key:
            record = await _lookup(session, x_fleet_api_key)
            try:
                valid = validate_record(record, now=dt.datetime.now(dt.UTC))
            except ApiKeyInvalid as exc:
                raise UnauthorizedError(str(exc)) from exc
            if scope not in valid.scopes:
                raise ForbiddenError(f"api key missing scope: {scope}")
            return CurrentServiceKey(id=valid.id, name=valid.name, scopes=valid.scopes)

        raise UnauthorizedError("missing bearer token or X-Fleet-Api-Key header")

    return _dep

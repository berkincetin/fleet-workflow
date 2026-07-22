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
from fleet_api.api_keys import ApiKeyInvalid, ApiKeyRecord, hash_key, validate_record
from fleet_api.db import get_session
from fleet_api.errors import ForbiddenError, UnauthorizedError
from fleet_api.models import ApiKey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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

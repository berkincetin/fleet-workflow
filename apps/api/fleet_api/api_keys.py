"""Fleet API key issuance/validation (task 6.1, TRD §7.1: "hashed, scoped, expiring").

Pure, transport-free helpers: generate a raw key + its stored hash, and decide
whether a presented raw key resolves to a still-usable row. The DB read/write
lives in the router/dependency (`routers/api_keys.py`, `service_auth.py`),
keeping this module unit-testable without Postgres — same split as
`registry.py`/`budget.py`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import secrets
from dataclasses import dataclass

_KEY_PREFIX = "fk"  # "fleet key" — lets a leaked-secret scanner recognize the shape


def generate_key() -> str:
    """Return a new raw key. Shown to the caller once; only its hash is stored."""
    return f"{_KEY_PREFIX}_{secrets.token_urlsafe(32)}"


def hash_key(raw_key: str) -> str:
    """Deterministic hash for storage/lookup — SHA-256 (not bcrypt: this is a
    high-entropy random token, not a low-entropy human password, so a fast
    hash is correct here and lets validation look the row up by exact hash
    match instead of scanning every row through a slow KDF)."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def keys_match(raw_key: str, stored_hash: str) -> bool:
    """Constant-time comparison of a presented key against a stored hash."""
    return hmac.compare_digest(hash_key(raw_key), stored_hash)


@dataclass
class ApiKeyRecord:
    """The subset of an `api_keys` row validation needs (DB-shape-agnostic)."""

    id: int
    name: str
    scopes: list[str]
    expires_at: dt.datetime | None
    revoked_at: dt.datetime | None


class ApiKeyInvalid(Exception):
    """Raised when a presented key doesn't resolve to a usable row."""


def validate_record(record: ApiKeyRecord | None, *, now: dt.datetime) -> ApiKeyRecord:
    """Decide whether `record` (already looked up by hash) is currently usable.

    Unknown hash, revoked, and expired all collapse to the same outward
    signal (401 "invalid or expired key") — the caller learns nothing about
    which case it was, matching TRD §7.1's "hashed, scoped, expiring" intent
    without leaking whether a given key ever existed.
    """
    if record is None:
        raise ApiKeyInvalid("unknown api key")
    if record.revoked_at is not None:
        raise ApiKeyInvalid("revoked api key")
    if record.expires_at is not None and record.expires_at <= now:
        raise ApiKeyInvalid("expired api key")
    return record


def has_scope(record: ApiKeyRecord, scope: str) -> bool:
    return scope in record.scopes

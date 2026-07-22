"""Unit tests for Fleet API key issuance/validation logic (task 6.1, TRD §7.1).

Pure hash/verify/validate logic — no DB. The router/dependency (which does the
actual lookup) is covered by tests/integration/test_api_keys_live.py.
"""

from __future__ import annotations

import datetime as dt

import pytest
from fleet_api.api_keys import (
    ApiKeyInvalid,
    ApiKeyRecord,
    generate_key,
    has_scope,
    hash_key,
    keys_match,
    validate_record,
)

_NOW = dt.datetime(2026, 7, 22, tzinfo=dt.UTC)


def _record(**over: object) -> ApiKeyRecord:
    base: dict[str, object] = dict(
        id=1, name="n8n", scopes=["pg_ro"], expires_at=None, revoked_at=None
    )
    base.update(over)
    return ApiKeyRecord(**base)  # type: ignore[arg-type]


def test_generate_key_is_unique_and_prefixed() -> None:
    a, b = generate_key(), generate_key()
    assert a != b
    assert a.startswith("fk_")


def test_hash_key_is_deterministic() -> None:
    raw = generate_key()
    assert hash_key(raw) == hash_key(raw)


def test_hash_key_differs_for_different_keys() -> None:
    assert hash_key(generate_key()) != hash_key(generate_key())


def test_keys_match_true_for_the_right_key() -> None:
    raw = generate_key()
    assert keys_match(raw, hash_key(raw)) is True


def test_keys_match_false_for_the_wrong_key() -> None:
    raw = generate_key()
    assert keys_match(generate_key(), hash_key(raw)) is False


def test_validate_record_accepts_a_healthy_key() -> None:
    record = _record()
    assert validate_record(record, now=_NOW) is record


def test_validate_record_rejects_unknown_hash() -> None:
    with pytest.raises(ApiKeyInvalid):
        validate_record(None, now=_NOW)


def test_validate_record_rejects_revoked_key() -> None:
    record = _record(revoked_at=_NOW - dt.timedelta(days=1))
    with pytest.raises(ApiKeyInvalid):
        validate_record(record, now=_NOW)


def test_validate_record_rejects_expired_key() -> None:
    record = _record(expires_at=_NOW - dt.timedelta(seconds=1))
    with pytest.raises(ApiKeyInvalid):
        validate_record(record, now=_NOW)


def test_validate_record_accepts_key_not_yet_expired() -> None:
    record = _record(expires_at=_NOW + dt.timedelta(days=1))
    assert validate_record(record, now=_NOW) is record


def test_has_scope() -> None:
    record = _record(scopes=["pg_ro", "invoice_intake"])
    assert has_scope(record, "pg_ro") is True
    assert has_scope(record, "slack_post") is False

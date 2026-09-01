"""fleet_api.users.get_or_create_user: JIT provisioning writes a real
`email_hash` (open item carried from Sprint 8).

From Sprint 1 until this fix the column was written as `""` unconditionally,
so its whole KVKK-pseudonymisation purpose was unmet — an erasure request
naming an email had nothing to match against. These tests pin the three
behaviours that fix depends on: hash on create, backfill on a later login for
rows provisioned before the fix, and never storing the raw address.

A fake session is used rather than a real one: the logic under test is which
value reaches the User row, not SQLAlchemy's persistence.
"""

from __future__ import annotations

from typing import Any

import pytest
from fleet_api.privacy import subject_hash
from fleet_api.users import get_or_create_user

_EMAIL = "Builder@Fleet.Local"


class _Result:
    def __init__(self, row: Any) -> None:
        self._row = row

    def scalar_one_or_none(self) -> Any:
        return self._row


class _FakeSession:
    """Returns `existing` from the lookup; records anything added/flushed."""

    def __init__(self, existing: Any = None) -> None:
        self._existing = existing
        self.added: list[Any] = []
        self.flushes = 0

    async def execute(self, *_args: Any, **_kwargs: Any) -> _Result:
        return _Result(self._existing)

    def add(self, row: Any) -> None:
        self.added.append(row)

    async def flush(self) -> None:
        self.flushes += 1


async def test_new_user_gets_hashed_email_never_the_address() -> None:
    session = _FakeSession()
    user = await get_or_create_user(session, kc_sub="sub-1", email=_EMAIL)

    assert user.email_hash == subject_hash(_EMAIL)
    # The whole point: the raw address must not survive anywhere on the row.
    assert _EMAIL not in str(user.__dict__.values())
    assert user.email_hash != _EMAIL


async def test_hash_is_case_and_whitespace_insensitive() -> None:
    """subject_hash normalises before hashing, so the same person logging in
    with differently-cased email still resolves to one erasure identity."""
    a = await get_or_create_user(_FakeSession(), kc_sub="s", email="  builder@fleet.local ")
    b = await get_or_create_user(_FakeSession(), kc_sub="s", email="BUILDER@FLEET.LOCAL")
    assert a.email_hash == b.email_hash


async def test_missing_email_claim_stays_empty_not_a_hash_of_none() -> None:
    """The column is NOT NULL, and a token without an `email` claim must not
    produce a hash of the string "None"."""
    user = await get_or_create_user(_FakeSession(), kc_sub="sub-2", email=None)
    assert user.email_hash == ""


class _ExistingUser:
    def __init__(self, email_hash: str) -> None:
        self.email_hash = email_hash
        self.kc_sub = "sub-3"


async def test_existing_user_with_empty_hash_is_backfilled_on_next_login() -> None:
    """Rows provisioned before this fix carry `""`; a later login fills them
    in, so no migration over pseudonymous data is needed."""
    existing = _ExistingUser(email_hash="")
    session = _FakeSession(existing=existing)

    returned = await get_or_create_user(session, kc_sub="sub-3", email=_EMAIL)

    assert returned is existing
    assert existing.email_hash == subject_hash(_EMAIL)
    assert session.added == [], "backfill must update in place, not insert a second row"


@pytest.mark.parametrize("email", [None, ""])
async def test_backfill_is_skipped_without_an_email_claim(email: str | None) -> None:
    existing = _ExistingUser(email_hash="")
    returned = await get_or_create_user(_FakeSession(existing=existing), kc_sub="s", email=email)
    assert returned.email_hash == ""


async def test_existing_hash_is_never_overwritten() -> None:
    """A already-populated hash stays put — re-hashing on every login would be
    wasted work, and an overwrite would mask a genuine identity change."""
    existing = _ExistingUser(email_hash="preexisting-hash")
    await get_or_create_user(_FakeSession(existing=existing), kc_sub="s", email=_EMAIL)
    assert existing.email_hash == "preexisting-hash"

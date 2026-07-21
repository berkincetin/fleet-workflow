"""Role derivation for the default model matrix (task 2.3 factory)."""

from __future__ import annotations

import pytest
from core.llm.factory import annotate_roles, derive_role


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("reasoning", "reasoning"),
        ("reasoning-fallback-1", "reasoning"),
        ("utility", "utility"),
        ("utility-fallback-2", "utility"),
        ("local-reasoning", "reasoning"),
        ("embeddings", "embeddings"),
        ("local-embeddings", "embeddings"),
    ],
)
def test_derive_role_maps_default_matrix_names(name: str, expected: str) -> None:
    assert derive_role(name) == expected


def test_annotate_roles_does_not_overwrite_existing_role() -> None:
    rows = [{"name": "utility", "fleet_role": "reasoning"}]
    assert annotate_roles(rows)[0]["fleet_role"] == "reasoning"


def test_annotate_roles_adds_missing_role() -> None:
    rows = [{"name": "utility"}]
    assert annotate_roles(rows)[0]["fleet_role"] == "utility"

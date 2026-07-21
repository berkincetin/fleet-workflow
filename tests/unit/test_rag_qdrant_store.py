"""Deterministic point-ID helper for the Qdrant store (task 3.1 dedup)."""

from __future__ import annotations

from fleet_rag.store.qdrant_store import collection_name, point_id_for


def test_point_id_is_deterministic_for_same_hash() -> None:
    assert point_id_for("abc123") == point_id_for("abc123")


def test_point_id_differs_for_different_hash() -> None:
    assert point_id_for("abc123") != point_id_for("def456")


def test_collection_name_namespaces_by_fleet_collection_id() -> None:
    assert collection_name(7) == "fleet_7"

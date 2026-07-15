"""Unit test: the ORM metadata declares the first-migration tables."""

from fleet_api.models import Base


def test_core_tables_declared() -> None:
    tables = set(Base.metadata.tables)
    assert {"departments", "users", "roles", "audit_log"} <= tables

"""Unit test: the ORM metadata declares the first-migration tables."""

from fleet_api.models import Base


def test_core_tables_declared() -> None:
    tables = set(Base.metadata.tables)
    assert {"departments", "users", "roles", "audit_log"} <= tables


def test_models_registry_table_declared() -> None:
    # Task 2.2: the model registry table (TRD §4.1).
    models = Base.metadata.tables["models"]
    cols = set(models.columns.keys())
    assert {
        "name",
        "provider",
        "litellm_model_id",
        "sensitivity_clearance",
        "status",
        "smoke_status",
    } <= cols

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


def test_rag_tables_declared() -> None:
    # Task 3.1/3.2: collections, documents, chunks (TRD §8, §11).
    tables = set(Base.metadata.tables)
    assert {"collections", "documents", "chunks"} <= tables

    collections = Base.metadata.tables["collections"]
    assert {"sensitivity", "retention_days", "pii_policy"} <= set(collections.columns.keys())

    documents = Base.metadata.tables["documents"]
    assert {"collection_id", "uri", "sha256", "ocr_status"} <= set(documents.columns.keys())

    chunks = Base.metadata.tables["chunks"]
    assert {
        "document_id",
        "content_sha256",
        "qdrant_point_id",
        "redacted",
        "original_sensitivity",
    } <= set(chunks.columns.keys())

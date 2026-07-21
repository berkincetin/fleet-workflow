"""RAG collections, documents, chunks (TRD §8, §11)

Revision ID: 0004_rag_collections
Revises: 0003_spend_and_budgets
Create Date: 2026-07-21
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_rag_collections"
down_revision: str | None = "0003_spend_and_budgets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("dept_id", sa.BigInteger(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("sensitivity", sa.String(32), nullable=False, server_default="internal"),
        sa.Column("retention_days", sa.Integer(), nullable=True),
        sa.Column("pii_policy", sa.String(32), nullable=False, server_default="redact"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("collection_id", sa.BigInteger(), sa.ForeignKey("collections.id"),
                  nullable=False),
        sa.Column("uri", sa.String(1024), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("ocr_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("meta", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_documents_collection_id", "documents", ["collection_id"])
    # Dedup-by-sha (AC 3.1: re-upload of the same doc costs 0 new embeddings).
    op.create_index(
        "uq_documents_collection_sha", "documents", ["collection_id", "sha256"], unique=True
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("qdrant_point_id", sa.String(64), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("redacted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("original_sensitivity", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("uq_chunks_qdrant_point_id", "chunks", ["qdrant_point_id"], unique=True)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chunks;")
    op.execute("DROP TABLE IF EXISTS documents;")
    op.execute("DROP TABLE IF EXISTS collections;")

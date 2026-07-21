"""models registry table (TRD §4.1)

Revision ID: 0002_models
Revises: 0001_initial
Create Date: 2026-07-21
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_models"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("litellm_model_id", sa.String(255), nullable=False),
        sa.Column("endpoint", sa.String(512), nullable=True),
        sa.Column("input_price_per_1k", sa.Numeric(12, 8), nullable=False),
        sa.Column("output_price_per_1k", sa.Numeric(12, 8), nullable=False),
        sa.Column("cached_input_price", sa.Numeric(12, 8), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=False),
        sa.Column("capabilities", sa.ARRAY(sa.String()), nullable=False,
                  server_default="{}"),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column("sensitivity_clearance", sa.String(32), nullable=False),
        sa.Column("region", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("smoke_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("smoke_detail", sa.String(1024), nullable=True),
        sa.Column("smoke_latency_ms", sa.Integer(), nullable=True),
        sa.Column("smoke_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS models;")

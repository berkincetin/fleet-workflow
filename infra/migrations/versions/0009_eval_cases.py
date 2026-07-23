"""eval_cases: examples gallery backing store (task 6.5.2, TRD §11 deferred eval_datasets shape)

Revision ID: 0009_eval_cases
Revises: 0008_api_keys
Create Date: 2026-07-22
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_eval_cases"
down_revision: str | None = "0008_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eval_cases",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("agent_name", sa.String(128), nullable=False),
        sa.Column("case_id", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="seed"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.UniqueConstraint("agent_name", "case_id", name="uq_eval_cases_agent_case"),
    )
    op.create_index("ix_eval_cases_agent_name", "eval_cases", ["agent_name"])


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS eval_cases;")

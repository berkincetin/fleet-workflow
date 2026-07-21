"""spend_ledger + budgets tables (TRD §5, §11)

Revision ID: 0003_spend_and_budgets
Revises: 0002_models
Create Date: 2026-07-21
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_spend_and_budgets"
down_revision: str | None = "0002_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "spend_ledger",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("agent_id", sa.String(128), nullable=True),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("dept_id", sa.String(128), nullable=True),
        sa.Column("tok_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tok_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tok_cached", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(14, 8), nullable=False, server_default="0"),
        sa.Column("trace_id", sa.String(255), nullable=True),
    )
    # Cost dashboard + budget pre-check both aggregate by scope over a period.
    op.create_index("ix_spend_ledger_ts", "spend_ledger", ["ts"])
    op.create_index("ix_spend_ledger_dept_ts", "spend_ledger", ["dept_id", "ts"])
    op.create_index("ix_spend_ledger_agent_ts", "spend_ledger", ["agent_id", "ts"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("scope_type", sa.String(16), nullable=False),
        sa.Column("scope_id", sa.String(128), nullable=True),
        sa.Column("period", sa.String(16), nullable=False, server_default="monthly"),
        sa.Column("limit_usd", sa.Numeric(14, 2), nullable=False),
        sa.Column("soft_pct", sa.Integer(), nullable=False, server_default="80"),
    )
    op.create_index(
        "uq_budget_scope", "budgets", ["scope_type", "scope_id", "period"], unique=True
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS budgets;")
    op.execute("DROP TABLE IF EXISTS spend_ledger;")

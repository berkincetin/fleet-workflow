"""automation_recipes: user-defined automations compiled to n8n workflows
(task 13.4, TRD §12). Fleet stores the recipe; `n8n_workflow_id` is only the
handle for the workflow compiled from it.

Revision ID: 0011_automation_recipes
Revises: 0010_subject_hash
Create Date: 2026-09-03
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_automation_recipes"
down_revision: str | None = "0010_subject_hash"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "automation_recipes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("n8n_workflow_id", sa.String(64), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_automation_recipes_name"),
    )


def downgrade() -> None:
    op.drop_table("automation_recipes")

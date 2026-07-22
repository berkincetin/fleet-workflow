"""api_keys: hashed, scoped, expiring programmatic credentials (task 6.1, TRD §7.1/§11)

Revision ID: 0008_api_keys
Revises: 0007_grant_readonly_to_fleet
Create Date: 2026-07-22
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_api_keys"
down_revision: str | None = "0007_grant_readonly_to_fleet"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hash", sa.String(255), nullable=False, unique=True),
        sa.Column("scopes", sa.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("dept_id", sa.BigInteger(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_api_keys_hash", "api_keys", ["hash"], unique=True)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS api_keys;")

"""initial: departments, users, roles, audit_log, and fleet_readonly role

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-15
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kc_sub", sa.String(255), nullable=False, unique=True),
        sa.Column("email_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("dept_id", sa.BigInteger(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("dept_id", sa.BigInteger(), sa.ForeignKey("departments.id"), nullable=True),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("entity", sa.String(255), nullable=True),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("trace_id", sa.String(255), nullable=True),
    )
    # Read-only role for the analytics MCP (CLAUDE.md rule 7). Idempotent create.
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fleet_readonly') THEN "
        "CREATE ROLE fleet_readonly NOLOGIN; END IF; END $$;"
    )
    op.execute("GRANT USAGE ON SCHEMA public TO fleet_readonly;")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO fleet_readonly;")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO fleet_readonly;"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_log;")
    op.execute("DROP TABLE IF EXISTS roles;")
    op.execute("DROP TABLE IF EXISTS users;")
    op.execute("DROP TABLE IF EXISTS departments;")
    op.execute("DROP ROLE IF EXISTS fleet_readonly;")

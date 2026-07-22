"""grant fleet_readonly to the connecting migration role (task 5.1 pg_ro MCP tool)

`fleet_readonly` (migration 0001) is NOLOGIN by design (CLAUDE.md rule 7) —
the pg_ro MCP tool connects as the normal app DB user and switches with
`SET ROLE fleet_readonly` per query, rather than giving the read-only role its
own login credentials. That switch requires the app user to be a member of
`fleet_readonly`, which no prior migration granted.

Grants to `current_user` (the role Alembic is actually connected as) rather
than a hardcoded `fleet` — the dev compose stack's app user is `fleet`, but
CI/tests run migrations as testcontainers' generated superuser (e.g. `test`),
and hardcoding `fleet` broke `alembic upgrade head` there with
`role "fleet" does not exist` (caught by test_migration_applies.py, which runs
against a real, isolated testcontainer with no `fleet` role at all).

Revision ID: 0007_grant_readonly_to_fleet
Revises: 0006_agent_collections
Create Date: 2026-07-22
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0007_grant_readonly_to_fleet"
down_revision: str | None = "0006_agent_collections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("GRANT fleet_readonly TO CURRENT_USER;")


def downgrade() -> None:
    op.execute("REVOKE fleet_readonly FROM CURRENT_USER;")

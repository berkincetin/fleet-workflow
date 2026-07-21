"""agents.collection_ids — which RAG collections an agent may retrieve from (task 4.4)

Revision ID: 0006_agent_collections
Revises: 0005_agents_chat_approvals
Create Date: 2026-07-22
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_agent_collections"
down_revision: str | None = "0005_agents_chat_approvals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "collection_ids", sa.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"
        ),
    )


def downgrade() -> None:
    op.drop_column("agents", "collection_ids")

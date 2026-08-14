"""subject_hash on documents/conversations: right-to-erasure lookup key
(task 8.3, TRD §8 "DELETE /v1/subjects/{hash} erases a person's
conversations/uploads"). Nullable — most documents (knowledge-base docs,
policies) have no single human "subject"; only person-linked uploads (e.g.
HR CVs, task 8.5) and conversations populate it.

Revision ID: 0010_subject_hash
Revises: 0009_eval_cases
Create Date: 2026-08-15
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_subject_hash"
down_revision: str | None = "0009_eval_cases"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("subject_hash", sa.String(64), nullable=True))
    op.create_index("ix_documents_subject_hash", "documents", ["subject_hash"])

    op.add_column("conversations", sa.Column("subject_hash", sa.String(64), nullable=True))
    op.create_index("ix_conversations_subject_hash", "conversations", ["subject_hash"])


def downgrade() -> None:
    op.drop_index("ix_conversations_subject_hash", table_name="conversations")
    op.drop_column("conversations", "subject_hash")

    op.drop_index("ix_documents_subject_hash", table_name="documents")
    op.drop_column("documents", "subject_hash")

"""Agents, prompt_versions, conversations, messages, feedback, approvals (TRD §9, §11)

Revision ID: 0005_agents_chat_approvals
Revises: 0004_rag_collections
Create Date: 2026-07-21
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_agents_chat_approvals"
down_revision: str | None = "0004_rag_collections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("dept_id", sa.BigInteger(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("reasoning_model", sa.String(128), nullable=False, server_default="reasoning"),
        sa.Column("utility_model", sa.String(128), nullable=False, server_default="utility"),
        sa.Column("sensitivity", sa.String(32), nullable=False, server_default="internal"),
        sa.Column("guardrail_policy_id", sa.String(128), nullable=True),
        sa.Column("semantic_cache", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "semantic_cache_threshold", sa.Numeric(4, 3), nullable=False, server_default="0.95"
        ),
        sa.Column("max_context_tokens", sa.Integer(), nullable=False, server_default="8000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.BigInteger(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("changelog", sa.String(1024), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("eval_run_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_prompt_versions_agent_id", "prompt_versions", ["agent_id"])
    op.create_index(
        "uq_prompt_versions_agent_version", "prompt_versions", ["agent_id", "version"],
        unique=True,
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.BigInteger(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_conversations_agent_id", "conversations", ["agent_id"])
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conv_id", sa.BigInteger(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("tool_trace", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(14, 8), nullable=False, server_default="0"),
        sa.Column("trace_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_messages_conv_id", "messages", ["conv_id"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("message_id", sa.BigInteger(), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_feedback_message_id", "feedback", ["message_id"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.BigInteger(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("run_id", sa.String(128), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("decided_by", sa.String(255), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index("ix_approvals_run_id", "approvals", ["run_id"])
    op.create_index("ix_approvals_status", "approvals", ["status"])


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS approvals;")
    op.execute("DROP TABLE IF EXISTS feedback;")
    op.execute("DROP TABLE IF EXISTS messages;")
    op.execute("DROP TABLE IF EXISTS conversations;")
    op.execute("DROP TABLE IF EXISTS prompt_versions;")
    op.execute("DROP TABLE IF EXISTS agents;")

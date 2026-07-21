"""SQLAlchemy declarative models for the first migration (users, departments, roles, audit_log)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all Fleet ORM models."""


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kc_sub: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dept_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    department: Mapped[Department | None] = relationship()


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    dept_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)


class Model(Base):
    """Model registry (TRD §4.1). Mirrored into the LiteLLM config."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    litellm_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    input_price_per_1k: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    output_price_per_1k: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    cached_input_price: Mapped[float | None] = mapped_column(Numeric(12, 8), nullable=True)
    context_window: Mapped[int] = mapped_column(Integer, nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    max_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    sensitivity_clearance: Mapped[str] = mapped_column(String(32), nullable=False)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    # Smoke-test-on-add result (§4.1).
    smoke_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    smoke_detail: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    smoke_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    smoke_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SpendLedger(Base):
    """Per-call LLM spend record (TRD §5 spend ledger, §11). Append-only."""

    __tablename__ = "spend_ledger"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dept_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tok_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tok_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tok_cached: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(14, 8), nullable=False, default=0)
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Budget(Base):
    """Spend budget for a scope (TRD §5 budget hierarchy, §11)."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scope_type: Mapped[str] = mapped_column(String(16), nullable=False)  # global|dept|agent|user
    scope_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    period: Mapped[str] = mapped_column(String(16), nullable=False, default="monthly")
    limit_usd: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    soft_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=80)


class Collection(Base):
    """RAG document collection (TRD §8 data classification, §11)."""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    dept_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    sensitivity: Mapped[str] = mapped_column(String(32), nullable=False, default="internal")
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # redact (default) | block | allow-local-only (§8 PII pipeline).
    pii_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="redact")
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Document(Base):
    """Uploaded source document (TRD §11)."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"), nullable=False)
    uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    ocr_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    collection: Mapped[Collection] = relationship()


class Chunk(Base):
    """Embedded, searchable slice of a document (TRD §8 redaction, §11)."""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    qdrant_point_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    redacted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_sensitivity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped[Document] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

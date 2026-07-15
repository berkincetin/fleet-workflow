# Sprint 1 · Stage B — CI + Migrations + Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement task 1.2 — a GitHub Actions PR pipeline (lint+typecheck → unit → testcontainers integration → security scans → build+scan image), an Alembic setup with a first migration (users, departments, roles, audit_log), and a seed script (synthetic data + analytics fixture warehouse views) — so every PR runs a real, non-skipped unit + integration suite in CI.

**Architecture:** Real Python deps join the `apps/api` uv package (SQLAlchemy 2 async + asyncpg, Alembic, Pydantic v2). Alembic lives under `infra/migrations/` (per CLAUDE.md layout) and targets the Postgres from the compose stack (local) or a testcontainer (CI/tests). An integration test spins up Postgres via `testcontainers` and asserts the migration + seed produce the expected tables/views. A minimal `apps/api` Dockerfile lets CI build+scan a real image. The CI workflow runs on every PR to `main`.

**Tech Stack:** Python 3.12 (uv), SQLAlchemy 2 (async) + asyncpg, Alembic, Pydantic v2, pytest + pytest-asyncio + testcontainers[postgres], GitHub Actions, trivy/bandit/gitleaks, Docker Buildx.

## Global Constraints

- **English only** in every repo artifact — code, comments, docs, config — regardless of chat language.
- **Python 3.12**, full typing, Pydantic v2 at boundaries, async I/O only. Domain errors will come from `core.errors` later; keep this stage's code minimal but typed.
- **Migrations only via Alembic** (CLAUDE.md rule 7). The `fleet_readonly` DB role stays read-only (analytics MCP) — create it in the migration and grant it only SELECT.
- **Docker image tags pinned** — never `:latest` (CI action versions pinned to a major, base images pinned).
- **No secrets in code/CI** — CI uses ephemeral testcontainer credentials or GitHub-provided tokens; no real secret is committed. gitleaks must pass.
- **Commit automatically in this repo** on `feat/sprint-1-stage-b` (single-sentence English subject, no AI byline, no `Co-Authored-By`). Never push to protected `main`; land via PR.
- **Seed data is synthetic only** — no real PII.
- PowerShell PATH refresh when a freshly-installed tool isn't found: `$m=[Environment]::GetEnvironmentVariable('Path','Machine');$u=[Environment]::GetEnvironmentVariable('Path','User');$env:Path="$m;$u"`.

---

### Task 1: Python deps + async DB layer in apps/api

**Files:**
- Modify: `apps/api/pyproject.toml` (add runtime deps)
- Modify: `pyproject.toml` (root — add test deps to the dev group)
- Create: `apps/api/fleet_api/__init__.py`
- Create: `apps/api/fleet_api/db.py` (async engine + session factory, settings from env)
- Create: `apps/api/fleet_api/models.py` (SQLAlchemy declarative models: Department, User, Role, AuditLog)
- Test: `tests/unit/test_models_metadata.py`

**Interfaces:**
- Consumes: uv workspace root (Task 1 of Stage A). `apps/api` is already a uv member with a stub `pyproject.toml` and `apps/api/__init__.py`.
- Produces: `fleet_api.db.get_engine(url: str) -> AsyncEngine`, `fleet_api.db.session_factory(engine) -> async_sessionmaker[AsyncSession]`, `fleet_api.db.database_url() -> str` (reads `FLEET_DATABASE_URL` env, defaults to the compose Postgres). `fleet_api.models.Base` (DeclarativeBase) with tables `departments`, `users`, `roles`, `audit_log`. Later tasks (migration autogen, seed, integration test) import `Base` and these models.

- [ ] **Step 1: Add runtime deps to `apps/api/pyproject.toml`**

Replace the `[project]` dependencies (keep name `fleet-api`, version, requires-python). The file becomes:
```toml
[project]
name = "fleet-api"
version = "0.1.0"
description = "Fleet API gateway (FastAPI)."
requires-python = ">=3.12"
dependencies = [
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["fleet_api"]
```

- [ ] **Step 2: Add test deps to the root `pyproject.toml` dev group**

In the root `pyproject.toml`, extend `[tool.uv] dev-dependencies` to add:
```toml
    "testcontainers[postgres]>=4.8",
    "psycopg2-binary>=2.9",
```
(psycopg2-binary is for Alembic's sync migration path; asyncpg is the app runtime driver. Keep the existing ruff/mypy/pytest/pytest-asyncio entries.)

- [ ] **Step 3: Create `apps/api/fleet_api/__init__.py`**

```python
"""Fleet API gateway package."""
```

- [ ] **Step 4: Create `apps/api/fleet_api/db.py`**

```python
"""Async database engine, session factory, and URL resolution for the Fleet API."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_DATABASE_URL = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"


def database_url() -> str:
    """Return the async database URL from FLEET_DATABASE_URL, or the local default."""
    return os.environ.get("FLEET_DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine(url: str | None = None) -> AsyncEngine:
    """Create an async engine for the given URL (defaults to database_url())."""
    return create_async_engine(url or database_url(), pool_pre_ping=True)


def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the given engine."""
    return async_sessionmaker(engine, expire_on_commit=False)
```

- [ ] **Step 5: Create `apps/api/fleet_api/models.py`**

```python
"""SQLAlchemy declarative models for the first migration (users, departments, roles, audit_log)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
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
```

- [ ] **Step 6: Write the failing unit test** `tests/unit/test_models_metadata.py`

```python
"""Unit test: the ORM metadata declares the first-migration tables."""

from fleet_api.models import Base


def test_core_tables_declared() -> None:
    tables = set(Base.metadata.tables)
    assert {"departments", "users", "roles", "audit_log"} <= tables
```

- [ ] **Step 7: Sync deps and run the unit test**

Run (PowerShell, PATH refreshed):
```
uv sync
uv run pytest tests/unit/test_models_metadata.py -v
```
Expected: `uv sync` installs the new deps; the test PASSES (imports resolve, all four tables present). If import of `fleet_api` fails, the `apps/api` package is not installed editable — confirm `uv sync` picked up `apps/api` as a workspace member.

- [ ] **Step 8: Run lint on the new code**

Run: `uv run ruff check apps/api tests`
Expected: exit 0 (fix any ruff finding in the new files before committing).

- [ ] **Step 9: Commit**

```
git add -A
git commit -m "Add async DB layer and ORM models for the first migration"
```

---

### Task 2: Alembic setup + first migration

**Files:**
- Create: `infra/migrations/alembic.ini`
- Create: `infra/migrations/env.py`
- Create: `infra/migrations/script.py.mako`
- Create: `infra/migrations/versions/0001_initial.py`
- Test: `tests/integration/test_migration_applies.py`

**Interfaces:**
- Consumes: `fleet_api.models.Base` and `fleet_api.db.database_url()` from Task 1.
- Produces: `alembic upgrade head` creates `departments`, `users`, `roles`, `audit_log`, and the read-only role `fleet_readonly` (granted SELECT). A helper `infra/migrations/env.py` that reads the DB URL from `FLEET_DATABASE_URL` (sync driver for Alembic). Later tasks (seed, integration test, CI) invoke `alembic -c infra/migrations/alembic.ini upgrade head`.

- [ ] **Step 1: Create `infra/migrations/alembic.ini`**

```ini
[alembic]
script_location = infra/migrations
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create `infra/migrations/env.py`** (Alembic uses a SYNC driver; convert the async URL)

```python
"""Alembic environment. Uses a sync psycopg2 URL derived from FLEET_DATABASE_URL."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from fleet_api.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_url() -> str:
    url = os.environ.get(
        "FLEET_DATABASE_URL",
        "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet",
    )
    # Alembic runs synchronously — swap the async driver for psycopg2.
    return url.replace("+asyncpg", "").replace("postgresql://", "postgresql+psycopg2://")


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _sync_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Create `infra/migrations/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 4: Create the first migration `infra/migrations/versions/0001_initial.py`** (hand-written, explicit — do not rely on autogenerate here)

```python
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
```

- [ ] **Step 5: Write the integration test** `tests/integration/test_migration_applies.py` (testcontainers Postgres)

```python
"""Integration test: `alembic upgrade head` creates the core tables and the readonly role."""

from __future__ import annotations

import os
import subprocess
import sys

import psycopg2
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def pg_url() -> str:
    with PostgresContainer("postgres:16") as pg:
        # testcontainers gives a psycopg2 URL; expose it for Alembic via env.
        raw = pg.get_connection_url()  # postgresql+psycopg2://test:test@host:port/test
        os.environ["FLEET_DATABASE_URL"] = raw
        yield raw


def test_migration_creates_core_tables(pg_url: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "infra/migrations/alembic.ini", "upgrade", "head"],
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    assert result.returncode == 0, result.stderr

    conn = psycopg2.connect(pg_url.replace("+psycopg2", ""))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public';"
        )
        tables = {row[0] for row in cur.fetchall()}
        assert {"departments", "users", "roles", "audit_log"} <= tables
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'fleet_readonly';")
        assert cur.fetchone() is not None
    finally:
        conn.close()
```

- [ ] **Step 6: Run the integration test locally (Docker required)**

Run (PowerShell, PATH refreshed, Docker running):
```
uv run pytest tests/integration/test_migration_applies.py -v
```
Expected: testcontainers pulls/starts `postgres:16`, `alembic upgrade head` exits 0, all four tables + the `fleet_readonly` role are found → PASS. If testcontainers can't reach Docker, ensure Docker Desktop is up; report the exact error, don't stub.

- [ ] **Step 7: Lint**

Run: `uv run ruff check infra tests`
Expected: exit 0.

- [ ] **Step 8: Commit**

```
git add -A
git commit -m "Add Alembic setup and initial migration for core tables and readonly role"
```

---

### Task 3: Seed script (synthetic data + analytics fixture views)

**Files:**
- Create: `apps/api/fleet_api/seed.py`
- Test: `tests/integration/test_seed_runs.py`

**Interfaces:**
- Consumes: `fleet_api.db` + `fleet_api.models` (Task 1); a migrated database (Task 2).
- Produces: `python -m fleet_api.seed` (idempotent) inserts synthetic departments/users/roles and creates the analytics fixture warehouse views (`fixture_sales`, `fixture_orders` — the views 5.2's analytics evals consume). Later CI calls it after `alembic upgrade head`.

- [ ] **Step 1: Create `apps/api/fleet_api/seed.py`**

```python
"""Seed synthetic data and analytics fixture warehouse views. Idempotent."""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from fleet_api.db import database_url, get_engine

_DEPARTMENTS = ["Customer Service", "Data", "Finance", "HR", "IT"]

_ANALYTICS_VIEWS = """
CREATE OR REPLACE VIEW fixture_sales AS
SELECT g AS id,
       (ARRAY['TR','DE','US','FR'])[1 + (g % 4)] AS region,
       (100 + (g * 37) % 900)::numeric AS amount_usd,
       (DATE '2026-01-01' + (g % 180)) AS sold_on
FROM generate_series(1, 500) AS g;

CREATE OR REPLACE VIEW fixture_orders AS
SELECT g AS id,
       1 + (g % 500) AS sale_id,
       (1 + (g % 5)) AS quantity,
       (g % 3 = 0) AS refunded
FROM generate_series(1, 500) AS g;
"""


async def seed() -> None:
    engine = get_engine(database_url())
    async with engine.begin() as conn:
        for name in _DEPARTMENTS:
            await conn.execute(
                text(
                    "INSERT INTO departments (name) VALUES (:n) "
                    "ON CONFLICT (name) DO NOTHING"
                ),
                {"n": name},
            )
        await conn.execute(
            text(
                "INSERT INTO users (kc_sub, email_hash, display_name, status) "
                "VALUES (:s, :e, :d, 'active') ON CONFLICT (kc_sub) DO NOTHING"
            ),
            {"s": "seed-admin", "e": "hash-admin", "d": "Seed Admin"},
        )
        # Analytics fixture views consumed by 5.2 evals (read via fleet_readonly).
        await conn.execute(text(_ANALYTICS_VIEWS))
        await conn.execute(
            text("GRANT SELECT ON fixture_sales, fixture_orders TO fleet_readonly")
        )
    await engine.dispose()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the integration test** `tests/integration/test_seed_runs.py`

```python
"""Integration test: seed inserts departments and creates the analytics fixture views."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import pytest
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

from fleet_api.db import get_engine
from fleet_api.seed import seed


@pytest.fixture(scope="module")
def migrated_pg() -> str:
    with PostgresContainer("postgres:16") as pg:
        raw = pg.get_connection_url()  # postgresql+psycopg2://...
        os.environ["FLEET_DATABASE_URL"] = raw
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c",
             "infra/migrations/alembic.ini", "upgrade", "head"],
            check=True,
            env={**os.environ},
        )
        # seed uses the async engine → hand it the asyncpg URL.
        os.environ["FLEET_DATABASE_URL"] = raw.replace("+psycopg2", "+asyncpg")
        yield os.environ["FLEET_DATABASE_URL"]


def test_seed_populates_and_creates_views(migrated_pg: str) -> None:
    asyncio.run(seed())

    async def _check() -> None:
        engine = get_engine(migrated_pg)
        async with engine.connect() as conn:
            depts = (await conn.execute(text("SELECT count(*) FROM departments"))).scalar_one()
            assert depts >= 5
            sales = (await conn.execute(text("SELECT count(*) FROM fixture_sales"))).scalar_one()
            assert sales == 500
        await engine.dispose()

    asyncio.run(_check())
```

- [ ] **Step 3: Run the seed integration test (Docker required)**

Run: `uv run pytest tests/integration/test_seed_runs.py -v`
Expected: PASS — migration applies, seed inserts ≥5 departments, `fixture_sales` has 500 rows.

- [ ] **Step 4: Lint**

Run: `uv run ruff check apps/api tests`
Expected: exit 0.

- [ ] **Step 5: Commit**

```
git add -A
git commit -m "Add idempotent seed script with analytics fixture warehouse views"
```

---

### Task 4: Makefile targets (test/migrate/seed/scan) + integration marker

**Files:**
- Modify: `Makefile` (add `migrate`, `seed`, `scan`; extend `test` to run integration too)
- Create: `pytest.ini` (register the `integration` marker; configure asyncio mode)

**Interfaces:**
- Consumes: Alembic (Task 2), seed (Task 3), the compose Postgres (Stage A).
- Produces: `make test` runs unit + integration; `make migrate` = `alembic upgrade head`; `make seed` = `python -m fleet_api.seed`; `make scan` = bandit + gitleaks (+ trivy if available). CI reuses these.

- [ ] **Step 1: Create `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
markers =
    integration: tests that require Docker (testcontainers).
testpaths = tests
```

- [ ] **Step 2: Extend `Makefile`** — replace the `test` target and append new ones. The `test` target becomes:

```makefile
test: ## unit + integration (testcontainers)
	uv run pytest tests/unit -q
	uv run pytest tests/integration -q

migrate: ## apply DB migrations (alembic upgrade head)
	uv run alembic -c infra/migrations/alembic.ini upgrade head

seed: ## load synthetic data + analytics fixture views
	uv run python -m fleet_api.seed

scan: ## security scans (bandit + gitleaks; trivy in CI)
	-uv run bandit -r apps packages -ll
	-gitleaks detect --no-banner --redact
```

(Keep the existing `dev`, `down`, `lint` targets and `.PHONY` — add `test migrate seed scan` to the `.PHONY` line.)

- [ ] **Step 3: Run `make migrate` + `make seed` against the compose Postgres**

Run (PowerShell, PATH refreshed, `make dev` stack up so Postgres is listening on 5432):
```
make dev
make migrate
make seed
```
Expected: `migrate` applies `0001_initial` (exit 0); `seed` inserts data + views (exit 0). If Postgres isn't up, `make dev` first. Tear down after with `make down` if you like.

- [ ] **Step 4: Run `make test` (unit + integration)**

Run: `make test`
Expected: unit passes; integration passes (testcontainers spins its own Postgres — independent of the compose one).

- [ ] **Step 5: Commit**

```
git add -A
git commit -m "Add migrate, seed, and scan Makefile targets and integration test marker"
```

---

### Task 5: Minimal apps/api Dockerfile

**Files:**
- Create: `apps/api/Dockerfile`
- Create: `apps/api/.dockerignore`

**Interfaces:**
- Consumes: the `apps/api` package + root uv workspace.
- Produces: a buildable image `fleet-api:dev` CI can build and scan with trivy. The image installs the `apps/api` deps and can run `python -m fleet_api.seed` / alembic; the HTTP server entrypoint lands in 1.3.

- [ ] **Step 1: Create `apps/api/.dockerignore`**

```
**/__pycache__
**/*.pyc
.venv
.git
node_modules
.next
tests
```

- [ ] **Step 2: Create `apps/api/Dockerfile`** (uv-based, pinned base)

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# Install uv (pinned) for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /bin/

WORKDIR /app

# Copy only the api package's metadata + source (build context is the repo root).
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/fleet_api apps/api/fleet_api
COPY infra/migrations infra/migrations

# Install the api package into a venv.
RUN uv pip install --system --no-cache ./apps/api

# Non-root user.
RUN useradd --create-home --uid 10001 fleet
USER fleet

# Placeholder entrypoint — the FastAPI server lands in task 1.3.
CMD ["python", "-c", "import fleet_api; print('fleet-api image OK')"]
```

- [ ] **Step 3: Build the image locally**

Run (from repo root, Docker running):
```
docker build -f apps/api/Dockerfile -t fleet-api:dev .
```
Expected: build succeeds; `docker run --rm fleet-api:dev` prints `fleet-api image OK`. If the `uv pip install` step fails on a dep, report the exact error — do not remove deps to force a pass.

- [ ] **Step 4: Commit**

```
git add -A
git commit -m "Add minimal apps/api Dockerfile for CI build and scan"
```

---

### Task 6: GitHub Actions CI pipeline

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: everything from Tasks 1–5 (uv workspace, Alembic, seed, Makefile, Dockerfile).
- Produces: a PR pipeline matching TRD §14 — `lint` → `unit` → `integration` (Docker-in-runner testcontainers) → `security` (bandit/gitleaks/trivy) → `build-image` (build + trivy scan). Runs on every PR to `main` and on pushes to feature branches.

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches-ignore: [main]

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.7.12"
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run mypy apps packages || true

  unit:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.7.12"
      - run: uv sync
      - run: uv run pytest tests/unit -q

  integration:
    runs-on: ubuntu-latest
    needs: unit
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.7.12"
      - run: uv sync
      # ubuntu-latest runners have Docker available for testcontainers.
      - run: uv run pytest tests/integration -q

  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.7.12"
      - run: uv sync
      - name: bandit
        run: uv run bandit -r apps packages -ll
      - name: gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_ENABLE_UPLOAD_ARTIFACT: "false"

  build-image:
    runs-on: ubuntu-latest
    needs: unit
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Build api image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: apps/api/Dockerfile
          tags: fleet-api:ci
          push: false
          load: true
      - name: Trivy scan
        uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: fleet-api:ci
          severity: HIGH,CRITICAL
          exit-code: "1"
          ignore-unfixed: true
```

- [ ] **Step 2: Validate the workflow YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('valid')"`
Expected: `valid`.

- [ ] **Step 3: Commit**

```
git add -A
git commit -m "Add GitHub Actions PR pipeline with lint, unit, integration, security, and image scan"
```

---

### Task 7: Verify CI on GitHub (push + watch)

**Files:** none (verification task; ends with a `docs/PROGRESS.md` entry).

**Interfaces:**
- Consumes: the pushed branch + `.github/workflows/ci.yml`.
- Produces: proof the pipeline runs green on GitHub (the real 1.2 AC — "integration job actually starts containers, not skipped").

- [ ] **Step 1: Push the branch and open the PR**

Run (gh is authenticated now):
```
git push -u origin feat/sprint-1-stage-b
gh pr create --base main --head feat/sprint-1-stage-b \
  --title "Sprint 1 · Stage B — CI, migrations, and seed" \
  --body "Implements task 1.2: GitHub Actions PR pipeline (lint → unit → integration(testcontainers) → security → build+scan), Alembic first migration (users/departments/roles/audit_log + fleet_readonly), and an idempotent seed with analytics fixture views."
```
Expected: PR created; Actions starts running.

- [ ] **Step 2: Watch the run to completion**

Run: `gh run watch` (or `gh pr checks --watch`).
Expected: all jobs (lint, unit, integration, security, build-image) succeed. The integration job must show testcontainers actually starting Postgres (not skipped). If a job fails, read its log with `gh run view --log-failed`, diagnose root cause, report — do NOT blindly retry.

- [ ] **Step 3: Write the `docs/PROGRESS.md` entry** for task 1.2 (append-only) — what was built, AC results (each CI job green, integration not skipped, migration+seed verified), issues, notes.

- [ ] **Step 4: Commit the PROGRESS entry**

```
git add docs/PROGRESS.md
git commit -m "Log task 1.2 completion with CI run results"
git push
```

---

## Self-Review

**1. Spec coverage (task 1.2 AC):** `make test` unit+integration in CI → Tasks 4, 6 (unit + integration jobs). Integration actually starts containers → Task 6 integration job (testcontainers on ubuntu-latest Docker) + Task 2/3 tests. Security jobs pass → Task 6 security job (bandit + gitleaks). Image build+scan passes → Task 5 Dockerfile + Task 6 build-image job (trivy). Alembic init + first migration (users, departments, roles, audit_log) → Task 2. Seed incl. analytics fixture views → Task 3. `make seed` loads fixture views → Tasks 3, 4. All AC items mapped.

**2. Placeholder scan:** No "TBD"/"implement later". Every file has full content. The Dockerfile CMD is a deliberate placeholder for the 1.3 server entrypoint and is labelled as such — not a plan gap.

**3. Type consistency:** `fleet_api.models.Base` (Task 1) is imported by Alembic `env.py` (Task 2) and used by the migration's table names, which match the models' `__tablename__` (departments/users/roles/audit_log). `FLEET_DATABASE_URL` is the single env var across db.py, env.py, seed.py, and both integration tests. The async URL (`+asyncpg`) vs sync URL (`+psycopg2`) conversion is handled consistently: Alembic strips async in `env.py`; the seed test swaps `+psycopg2`→`+asyncpg` before calling the async seed. `fleet_readonly` role name is identical in the migration and the CLAUDE.md rule. uv version `0.7.12` is pinned identically in the Dockerfile and all CI jobs.

**Note on a known risk:** testcontainers-python's `PostgresContainer.get_connection_url()` returns a `postgresql+psycopg2://` URL by default; both integration tests rely on that exact format for their `+psycopg2`↔`+asyncpg` swaps. If the installed testcontainers version returns a bare `postgresql://`, the swaps still work (env.py adds `+psycopg2`; the seed test's `.replace("+psycopg2","+asyncpg")` would no-op and the async engine would fail). Task 2 Step 6 and Task 3 Step 3 run these locally FIRST, so any format mismatch surfaces during local verification before CI — the implementer must not skip the local runs.

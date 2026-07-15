# Sprint 1 · Stage A — Monorepo Skeleton + Dev Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the Fleet monorepo skeleton and a `docker-compose.dev.yml` that boots the full 11-service local dev stack, driven by a Makefile, so `make dev` brings everything up and later sprints have a foundation to build on.

**Architecture:** A `uv` Python workspace (root `pyproject.toml`) + `pnpm` JS workspace side by side in one repo. Infrastructure lives under `infra/compose/` (compose file + per-service config: Keycloak realm, Grafana/Prometheus/Loki provisioning). A root `Makefile` wraps the common commands. Application packages are created as empty skeletons only; their code lands in later sprints. Task 1.0's `pre-push` git hook is set up first as the quality gate.

**Tech Stack:** Python 3.12 (via `uv`), `ruff` + `mypy`, `pnpm` + Next.js 15/TS, Docker Compose, GNU Make, Keycloak 26, Postgres 16, Grafana/Prometheus/Loki/Alertmanager, Qdrant, MinIO, Redis 7, LiteLLM, Langfuse 2, Mailpit.

## Global Constraints

- **English only** in every repo artifact — code, comments, docs, config — regardless of chat language.
- **Python 3.12**, full typing, async I/O only (applies once real code lands; skeletons are minimal).
- **Docker image tags are pinned** to a fixed major/minor — never `:latest` — so `make dev` is reproducible.
- **Commit convention:** single-sentence English subject, no `Claude`/AI byline, no `Co-Authored-By` trailer. **Do NOT run `git commit`** — prepare the message and stop for the user, unless they say "commit'i at".
- **`docs/` is not touched** — it already exists (source/, split/, originals) and is canonical.
- **This stage ships no application logic** — skeleton packages only (YAGNI); no eval, no business code.
- Run commands on Windows PowerShell with a PATH refresh helper when a new tool was just installed:
  `$m=[Environment]::GetEnvironmentVariable('Path','Machine');$u=[Environment]::GetEnvironmentVariable('Path','User');$env:Path="$m;$u"`.

---

### Task 1: Root workspace files (uv + pnpm + tooling config)

**Files:**
- Create: `pyproject.toml` (root uv workspace + ruff + mypy config)
- Create: `pnpm-workspace.yaml`
- Create: `package.json` (root, private, workspace scripts)
- Create: `.gitignore`
- Create: `.python-version` (`3.12`)
- Create: `README.md` — **modify existing** (append dev-setup bootstrap section; final version in task 10.1)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `uv` workspace root that later Python packages join via `[tool.uv.workspace] members`; `pnpm` workspace root that later JS packages join via `packages:`; `ruff`/`mypy` config all Python tasks inherit.

- [ ] **Step 1: Create `.python-version`**

```
3.12
```

- [ ] **Step 2: Create root `pyproject.toml`**

```toml
[project]
name = "fleet"
version = "0.1.0"
description = "Fleet — internal AI operations platform (monorepo root)"
requires-python = ">=3.12"
readme = "README.md"

[tool.uv.workspace]
members = ["apps/*", "packages/*"]

[tool.uv]
# dev dependencies shared across the workspace
dev-dependencies = [
    "ruff>=0.6",
    "mypy>=1.11",
    "pytest>=8",
    "pytest-asyncio>=0.24",
]

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["apps", "packages"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "ASYNC"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

- [ ] **Step 3: Create `pnpm-workspace.yaml`**

```yaml
packages:
  - "apps/web"
  - "packages/*"
```

- [ ] **Step 4: Create root `package.json`**

```json
{
  "name": "fleet",
  "private": true,
  "packageManager": "pnpm@10.6.5",
  "scripts": {
    "lint": "pnpm -r --if-present lint",
    "build": "pnpm -r --if-present build"
  }
}
```

- [ ] **Step 5: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
.mypy_cache/
.ruff_cache/
.pytest_cache/
# Node
node_modules/
.next/
# Env / secrets
.env
.env.*
!.env.example
# Build / data
dist/
*.egg-info/
# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 6: Append a bootstrap dev-setup section to `README.md`** (keep the existing top; add below it)

```markdown

## Dev setup (bootstrap — finalized in task 10.1)

Prerequisites: Docker Desktop, `uv`, `pnpm`, GNU Make.

```bash
uv sync            # create the Python venv and install workspace + dev deps
pnpm install       # install JS workspace deps
make dev           # boot the full local stack (docker compose)
```

The four environments (`local` compose, `test`, `demo/staging`, `prod`) share one Helm
chart with per-env values; only `local` runs during development (see docs/TECHNICAL_REQUIREMENTS.md §14).
```

- [ ] **Step 7: Verify uv resolves the workspace**

Run (PowerShell, PATH refreshed):
```
uv sync
```
Expected: creates `.venv/`, installs ruff/mypy/pytest, exits 0. (No members yet — that is fine.)

- [ ] **Step 8: Prepare commit message (do NOT commit)**

Message: `Add uv/pnpm monorepo workspace root with ruff, mypy, and gitignore`
Stop and report; the user commits.

---

### Task 2: Directory skeleton for all app/packages/infra trees

**Files:**
- Create: `apps/api/__init__.py`, `apps/api/README.md`
- Create: `apps/runtime/__init__.py`, `apps/runtime/README.md`
- Create: `apps/rag/__init__.py`, `apps/rag/README.md`
- Create: `apps/mcp/__init__.py`, `apps/mcp/README.md`
- Create: `apps/web/README.md` (JS skeleton done in task 3)
- Create: `packages/shared/README.md`
- Create: `gateway/litellm/.gitkeep`
- Create: `workflows/.gitkeep`
- Create: `infra/compose/.gitkeep`, `infra/helm/fleet/.gitkeep`, `infra/k3d/.gitkeep`, `infra/migrations/.gitkeep`
- Create: `evals/.gitkeep`
- Create: `tests/unit/.gitkeep`, `tests/integration/.gitkeep`, `tests/e2e/.gitkeep`, `tests/load/.gitkeep`, `tests/security/.gitkeep`

**Interfaces:**
- Consumes: workspace root from Task 1 (`[tool.uv.workspace] members = ["apps/*", "packages/*"]`).
- Produces: the full CLAUDE.md Repository Layout tree; each Python app is an importable package (has `__init__.py`); later sprints fill internals.

- [ ] **Step 1: Create each Python app package `__init__.py`** (identical minimal content, one per app)

For `apps/api/__init__.py`, `apps/runtime/__init__.py`, `apps/rag/__init__.py`, `apps/mcp/__init__.py`:
```python
"""Fleet <app> package. Skeleton — implementation lands in its sprint."""
```
(replace `<app>` with the app name: api, runtime, rag, mcp.)

- [ ] **Step 2: Create a one-line README.md in each app/package dir** stating its purpose and the sprint that fills it. Example for `apps/api/README.md`:

```markdown
# apps/api — FastAPI gateway

Skeleton. Auth core lands in task 1.3; routers/services/middleware follow.
```

Do the same for `runtime` (Sprint 4), `rag` (Sprint 3), `mcp` (Sprint 5), `web` (Sprint 3+), `packages/shared` (generated in 1.4).

- [ ] **Step 3: Create `.gitkeep` placeholders** for dirs with no files yet (gateway/litellm, workflows, infra/*, evals, tests/*).

Run:
```
git add -A && git status --short
```
Expected: every skeleton dir shows as a new tracked path.

- [ ] **Step 4: Verify uv still resolves with members present**

Run: `uv sync`
Expected: exits 0; app packages recognized as workspace members (they have no deps yet).

- [ ] **Step 5: Prepare commit message (do NOT commit)**

Message: `Scaffold monorepo directory tree for apps, packages, infra, evals, and tests`

---

### Task 3: Next.js 15 web skeleton (pnpm)

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/.eslintrc.json` (or `eslint.config.mjs`)

**Interfaces:**
- Consumes: `pnpm-workspace.yaml` from Task 1 (declares `apps/web`).
- Produces: a buildable Next.js app so `pnpm --filter web build` and `pnpm --filter web lint` succeed; the shell that Sprint 3+ screens plug into.

- [ ] **Step 1: Create `apps/web/package.json`**

```json
{
  "name": "web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "next": "15.1.0",
    "react": "19.0.0",
    "react-dom": "19.0.0"
  },
  "devDependencies": {
    "typescript": "5.7.2",
    "@types/node": "22.10.0",
    "@types/react": "19.0.0",
    "@types/react-dom": "19.0.0",
    "eslint": "9.17.0",
    "eslint-config-next": "15.1.0"
  }
}
```

- [ ] **Step 2: Create `apps/web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Create `apps/web/next.config.ts`**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

- [ ] **Step 4: Create `apps/web/app/layout.tsx`**

```tsx
export const metadata = {
  title: "Fleet",
  description: "Internal AI operations platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 5: Create `apps/web/app/page.tsx`**

```tsx
export default function Home() {
  return <main>Fleet platform — web shell. Screens land in Sprint 3+.</main>;
}
```

- [ ] **Step 6: Create `apps/web/eslint.config.mjs`**

```javascript
import next from "eslint-config-next";

export default [...next()];
```

- [ ] **Step 7: Install and verify build + lint**

Run:
```
pnpm install
pnpm --filter web build
pnpm --filter web lint
```
Expected: `pnpm install` links the workspace; `build` produces `.next/` and exits 0; `lint` exits 0.

- [ ] **Step 8: Prepare commit message (do NOT commit)**

Message: `Add Next.js 15 TypeScript web app skeleton`

---

### Task 4: Environment template + Keycloak realm

**Files:**
- Create: `.env.example`
- Create: `infra/compose/keycloak/fleet-realm.json`

**Interfaces:**
- Consumes: nothing structural.
- Produces: `.env.example` documenting every var the compose stack reads; a Keycloak realm imported at container start with 5 test users (admin, builder, approver + 2 regular).

- [ ] **Step 1: Create `.env.example`** (documents all stack vars; real `.env` is gitignored)

```dotenv
# Postgres
POSTGRES_USER=fleet
POSTGRES_PASSWORD=fleet_dev_pw
POSTGRES_DB=fleet
# Keycloak admin
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
# MinIO
MINIO_ROOT_USER=fleet
MINIO_ROOT_PASSWORD=fleet_dev_pw
# Langfuse
LANGFUSE_SALT=changeme_dev_salt
NEXTAUTH_SECRET=changeme_dev_secret
# Grafana
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
```

- [ ] **Step 2: Create `infra/compose/keycloak/fleet-realm.json`** — a realm named `fleet` with a client `fleet-api` and 5 users. Full content:

```json
{
  "realm": "fleet",
  "enabled": true,
  "sslRequired": "none",
  "clients": [
    {
      "clientId": "fleet-api",
      "enabled": true,
      "publicClient": false,
      "secret": "fleet-api-dev-secret",
      "directAccessGrantsEnabled": true,
      "standardFlowEnabled": true,
      "redirectUris": ["http://localhost:3000/*"],
      "webOrigins": ["http://localhost:3000"]
    }
  ],
  "roles": {
    "realm": [
      { "name": "admin" },
      { "name": "builder" },
      { "name": "approver" },
      { "name": "user" }
    ]
  },
  "users": [
    {
      "username": "admin",
      "enabled": true,
      "email": "admin@fleet.local",
      "firstName": "Admin",
      "lastName": "User",
      "credentials": [{ "type": "password", "value": "admin", "temporary": false }],
      "realmRoles": ["admin", "user"]
    },
    {
      "username": "builder",
      "enabled": true,
      "email": "builder@fleet.local",
      "firstName": "Builder",
      "lastName": "User",
      "credentials": [{ "type": "password", "value": "builder", "temporary": false }],
      "realmRoles": ["builder", "user"]
    },
    {
      "username": "approver",
      "enabled": true,
      "email": "approver@fleet.local",
      "firstName": "Approver",
      "lastName": "User",
      "credentials": [{ "type": "password", "value": "approver", "temporary": false }],
      "realmRoles": ["approver", "user"]
    },
    {
      "username": "user1",
      "enabled": true,
      "email": "user1@fleet.local",
      "firstName": "Regular",
      "lastName": "One",
      "credentials": [{ "type": "password", "value": "user1", "temporary": false }],
      "realmRoles": ["user"]
    },
    {
      "username": "user2",
      "enabled": true,
      "email": "user2@fleet.local",
      "firstName": "Regular",
      "lastName": "Two",
      "credentials": [{ "type": "password", "value": "user2", "temporary": false }],
      "realmRoles": ["user"]
    }
  ]
}
```

- [ ] **Step 3: Validate the realm JSON is well-formed**

Run: `python -c "import json; json.load(open('infra/compose/keycloak/fleet-realm.json')); print('valid')"`
Expected: `valid`

- [ ] **Step 4: Prepare commit message (do NOT commit)**

Message: `Add env template and Keycloak fleet realm with five test users`

---

### Task 5: Observability provisioning files (Prometheus, Grafana, Loki, Alertmanager)

**Files:**
- Create: `infra/compose/prometheus/prometheus.yml`
- Create: `infra/compose/grafana/provisioning/datasources/datasources.yml`
- Create: `infra/compose/loki/loki-config.yml`
- Create: `infra/compose/alertmanager/alertmanager.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: config files mounted into the observability containers so Grafana comes up with Prometheus + Loki datasources already wired (1.1 AC).

- [ ] **Step 1: Create `infra/compose/prometheus/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]
```

- [ ] **Step 2: Create `infra/compose/grafana/provisioning/datasources/datasources.yml`**

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

- [ ] **Step 3: Create `infra/compose/loki/loki-config.yml`** (minimal single-binary dev config)

```yaml
auth_enabled: false
server:
  http_listen_port: 3100
common:
  instance_addr: 127.0.0.1
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory
schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
```

- [ ] **Step 4: Create `infra/compose/alertmanager/alertmanager.yml`** (minimal, routes to a null receiver in dev)

```yaml
route:
  receiver: "devnull"
receivers:
  - name: "devnull"
```

- [ ] **Step 5: Validate all YAML parses**

Run:
```
python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('infra/compose/**/*.yml', recursive=True)]; print('all valid')"
```
Expected: `all valid` (install pyyaml first if missing: `uv pip install pyyaml` inside the venv, or `python -m pip install pyyaml`).

- [ ] **Step 6: Prepare commit message (do NOT commit)**

Message: `Add Prometheus, Grafana, Loki, and Alertmanager provisioning config`

---

### Task 6: `docker-compose.dev.yml` — the 11-service stack

**Files:**
- Create: `infra/compose/docker-compose.dev.yml`

**Interfaces:**
- Consumes: `.env.example` vars (Task 4), Keycloak realm (Task 4), observability config (Task 5).
- Produces: the local dev stack `make dev` boots; every later task's integration/AC checks run against these containers.

- [ ] **Step 1: Create `infra/compose/docker-compose.dev.yml`** with all 11 services, pinned images, healthchecks, named volumes, and config mounts. Full content:

```yaml
name: fleet-dev

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-fleet}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-fleet_dev_pw}
      POSTGRES_DB: ${POSTGRES_DB:-fleet}
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-fleet}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  qdrant:
    image: qdrant/qdrant:v1.12.4
    ports: ["6333:6333", "6334:6334"]
    volumes: ["qdrantdata:/qdrant/storage"]

  minio:
    image: minio/minio:RELEASE.2024-12-13T22-19-12Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-fleet}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-fleet_dev_pw}
    ports: ["9000:9000", "9001:9001"]
    volumes: ["miniodata:/data"]
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 10

  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    command: ["start-dev", "--import-realm"]
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: ${KEYCLOAK_ADMIN:-admin}
      KC_BOOTSTRAP_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD:-admin}
    ports: ["8080:8080"]
    volumes:
      - ./keycloak:/opt/keycloak/data/import:ro

  litellm:
    image: ghcr.io/berriai/litellm:main-v1.53.7-stable
    ports: ["4000:4000"]
    command: ["--port", "4000"]

  langfuse:
    image: langfuse/langfuse:2
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-fleet}:${POSTGRES_PASSWORD:-fleet_dev_pw}@postgres:5432/${POSTGRES_DB:-fleet}
      NEXTAUTH_URL: http://localhost:3001
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET:-changeme_dev_secret}
      SALT: ${LANGFUSE_SALT:-changeme_dev_salt}
      TELEMETRY_ENABLED: "false"
    ports: ["3001:3000"]

  prometheus:
    image: prom/prometheus:v3.0.1
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana:11.4.0
    environment:
      GF_SECURITY_ADMIN_USER: ${GF_SECURITY_ADMIN_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GF_SECURITY_ADMIN_PASSWORD:-admin}
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    ports: ["3002:3000"]
    depends_on: [prometheus, loki]

  loki:
    image: grafana/loki:3.3.2
    command: ["-config.file=/etc/loki/loki-config.yml"]
    volumes:
      - ./loki/loki-config.yml:/etc/loki/loki-config.yml:ro
    ports: ["3100:3100"]

  alertmanager:
    image: prom/alertmanager:v0.28.0
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    ports: ["9093:9093"]

  mailpit:
    image: axllent/mailpit:v1.21.8
    ports: ["1025:1025", "8025:8025"]

volumes:
  pgdata:
  qdrantdata:
  miniodata:
```

- [ ] **Step 2: Validate compose file syntax**

Run (from `infra/compose/`, with `.env` copied from `.env.example`):
```
cp .env.example ../../.env 2>/dev/null; docker compose -f infra/compose/docker-compose.dev.yml config --quiet
```
Expected: exits 0, no error (validates references and env interpolation).

- [ ] **Step 3: Prepare commit message (do NOT commit)**

Message: `Add docker-compose dev stack with eleven pinned services`

---

### Task 7: Makefile + task 1.0 pre-push hook

**Files:**
- Create: `Makefile`
- Create: `.githooks/pre-push`

**Interfaces:**
- Consumes: compose file (Task 6), `pyproject.toml`/`package.json` (Task 1).
- Produces: `make dev|down|lint` targets; a `pre-push` hook that runs `make lint` + unit tests and blocks a failing push. Later stages append `test|migrate|seed|scan|k3d-up`.

- [ ] **Step 1: Create root `Makefile`** (Stage A targets; later targets added in their stages)

```makefile
COMPOSE := docker compose -f infra/compose/docker-compose.dev.yml

.PHONY: dev down lint test

dev: ## boot the full local dev stack
	$(COMPOSE) up -d

down: ## stop the dev stack
	$(COMPOSE) down

lint: ## ruff + mypy (Python) and eslint + tsc (web)
	uv run ruff check .
	uv run mypy apps packages || true
	pnpm -r --if-present lint

test: ## unit + integration (wired up in Stage B)
	uv run pytest tests/unit -q
```

Note: `mypy ... || true` is a temporary Stage-A allowance because skeleton packages have no typed code yet; Stage C tightens this once real modules exist.

- [ ] **Step 2: Create `.githooks/pre-push`** (task 1.0 quality gate)

```bash
#!/usr/bin/env bash
# Fleet pre-push hook — block a push if lint or unit tests fail.
set -euo pipefail

echo "[pre-push] running lint..."
make lint

echo "[pre-push] running unit tests..."
make test

echo "[pre-push] OK"
```

- [ ] **Step 3: Activate the hooks path and make the hook executable**

Run:
```
git config core.hooksPath .githooks
git update-index --chmod=+x .githooks/pre-push 2>/dev/null || true
chmod +x .githooks/pre-push 2>/dev/null || true
```
Expected: `git config --get core.hooksPath` returns `.githooks`.

- [ ] **Step 4: Verify `make lint` runs** (with an empty/skeleton codebase)

Run: `make lint`
Expected: ruff reports no errors on the skeleton; exits 0 (mypy softened, pnpm lint runs web).

- [ ] **Step 5: Verify `make test` runs** (no unit tests yet → pytest exits 5 "no tests collected"; add a trivial smoke test so it is green)

Create `tests/unit/test_smoke.py`:
```python
def test_smoke() -> None:
    assert True
```
Run: `make test`
Expected: 1 passed.

- [ ] **Step 6: Prepare commit message (do NOT commit)**

Message: `Add Makefile targets and pre-push lint/test git hook`

---

### Task 8: Live stack verification (`make dev`) — Stage A acceptance

**Files:**
- None (verification task). Optionally create: `docs/PROGRESS.md` (first entry after this task).

**Interfaces:**
- Consumes: everything from Tasks 1–7.
- Produces: proof that the 1.1 AC holds against real containers.

- [ ] **Step 1: Copy env and boot the stack**

Run:
```
cp .env.example .env
make dev
```
Expected: `docker compose ... up -d` creates all 11 services; exits 0.

- [ ] **Step 2: Wait for health and list services**

Run: `docker compose -f infra/compose/docker-compose.dev.yml ps`
Expected: postgres/redis/minio show healthy; all 11 containers `running`. Investigate any that exited (report; do not silently patch — Task Execution Protocol step 5).

- [ ] **Step 3: Verify Keycloak realm imported (5 users)**

Open `http://localhost:8080` → admin console (admin/admin) → realm `fleet` exists with users admin, builder, approver, user1, user2. Or via container log grep: `docker compose -f infra/compose/docker-compose.dev.yml logs keycloak | grep -i "Imported realm fleet"`.
Expected: realm `fleet` present with the 5 users.

- [ ] **Step 4: Verify Grafana datasources provisioned**

Open `http://localhost:3002` (admin/admin) → Connections → Data sources → Prometheus (default) + Loki present.
Expected: both datasources listed, no "not found" errors.

- [ ] **Step 5: Verify mailpit reachable**

Open `http://localhost:8025`.
Expected: Mailpit UI loads.

- [ ] **Step 6: Tear down**

Run: `make down`
Expected: stack stops cleanly.

- [ ] **Step 7: Write the Stage-A findings report + PROGRESS entry**

Create `docs/PROGRESS.md` with the first entry (per CLAUDE.md Task Execution Protocol step 6 format): task 1.0 + 1.1, what was built, AC results (per step above), issues (with root cause if any), notes. Status DONE/PARTIAL/BLOCKED.

- [ ] **Step 8: Prepare commit message (do NOT commit) and STOP for user**

Message: `Boot and verify the eleven-service local dev stack`
Report Stage-A results to the user and wait for approval before Stage B.

---

## Self-Review

**1. Spec coverage:** Spec Stage A = task 1.0 (git hook + convention) + task 1.1 (skeleton, compose 11 services, Makefile, Keycloak realm, Grafana/Prom/Loki provisioning). Mapped: workspace root → Task 1; dir tree → Task 2; web skeleton → Task 3; env + Keycloak realm → Task 4; observability provisioning → Task 5; compose 11 services → Task 6; Makefile + pre-push hook (1.0) → Task 7; live `make dev` AC verification → Task 8. Branch protection (GitHub side of 1.0) is correctly deferred to Stage C per the spec — not in this plan. No gaps.

**2. Placeholder scan:** No "TBD"/"implement later" left as work. The `mypy ... || true` and the smoke test are explicit, justified interim measures, not placeholders. Every config file has full content.

**3. Type consistency:** Service names in the compose file (postgres, redis, qdrant, minio, keycloak, litellm, langfuse, prometheus, grafana, loki, alertmanager, mailpit) match the datasource URLs (http://prometheus:9090, http://loki:3100) and the Makefile `COMPOSE` path. Realm name `fleet` and client `fleet-api` are consistent across Task 4 and the `.env.example`. Ports are unique (5432, 6379, 6333/6334, 9000/9001, 8080, 4000, 3001, 9090, 3002, 3100, 9093, 1025/8025).

**Note on ports:** Grafana is mapped to host `3002` and Langfuse to `3001` (both listen on container `3000`) to avoid collision with the web app's dev `3000`. Documented here so later tasks use the same host ports.

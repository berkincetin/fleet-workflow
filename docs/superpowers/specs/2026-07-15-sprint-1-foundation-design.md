# Sprint 1 Foundation — Design Spec

**Date:** 2026-07-15
**Scope:** IMPLEMENTATION_PLAN Sprint 1 (tasks 1.0–1.5) plus the git bootstrap parts of task 1.0.
**Status:** Approved for implementation.

## Goal

Stand up the Fleet monorepo foundation so that later sprints can build on a booting local
stack, a working CI gate, gateway auth, cross-cutting middleware, and a Helm/k3d skeleton.
This sprint writes **skeleton + infrastructure only** — application logic for each app package
lands in its own later sprint. The definition of success is: the full dev stack boots, CI runs
a real (not skipped) unit + integration suite, the API gateway authenticates and enforces RBAC,
and the same stack deploys to a local k3d cluster from one Helm chart.

Everything committed to the repo (code, comments, docs) is written in **English only**, regardless
of the chat language.

## Decisions (locked with the user)

- **Python tooling:** `uv` workspace + `ruff` (lint/format) + `mypy` (types). Python 3.12.
- **JS tooling:** `pnpm` workspaces. Next.js 15 + TypeScript.
- **Ordering:** build skeleton + CI first (1.1, 1.2); defer GitHub branch protection (the GitHub
  side of 1.0) to the end of the sprint, once the CI checks it must require actually exist.
  The local `pre-push` hook and commit convention are set up at the start (task 1.0).
- **Docker:** available and running on the user's machine → every AC is verified live against the
  running stack, not just against mocks.
- **Delivery rhythm:** three task-group stages, each ending with a stop-verify-report-approve gate.

## Delivery Stages

| Stage | Tasks | Live verification (Docker) |
|---|---|---|
| **A** | 1.0 (git hook + convention) · 1.1 monorepo skeleton + `docker-compose.dev.yml` (11 services) + Makefile + Keycloak realm + Grafana/Prometheus/Loki provisioning | `make dev` boots the full stack incl. mailpit; Keycloak realm imported (5 test users incl. admin/builder/approver); Grafana reachable with Prometheus + Loki datasources provisioned |
| **B** | 1.2 GitHub Actions CI (lint+typecheck → unit → testcontainers integration → security scans → build+scan images) + Alembic init + first migration (users, departments, roles, audit_log) + seed script (incl. analytics fixture warehouse views) | `make test` (unit **and** testcontainers integration) passes; CI actually starts containers (not skipped); security jobs pass (no high severity); image build+scan passes; `make seed` loads demo data incl. fixture views |
| **C** | 1.3 gateway auth core (app factory, OIDC validation, RBAC decorator + permission service, error model, health/readiness) · 1.4 middleware (append-only audit, OpenTelemetry trace_id in/out, Redis rate limiter, OpenAPI → generated TS client in `packages/shared`) · 1.5 Helm umbrella chart + k3d bootstrap + `values-dev.yaml` · **then** GitHub branch protection on `main` | integration tests cover 401/403; audit row written with trace_id; rate-limit 429 test; traces exported and inspectable (OTel logging exporter in dev); `make k3d-up` brings up the 1.1 stack on local k3d from the chart |

## Repository Layout

Follows CLAUDE.md Repository Layout exactly. The full tree is created in Stage A; package
internals fill in over later sprints — Stage A places only skeleton/placeholder modules.

```
fleet/                     (repo root — the existing fleet-workflow/)
├── apps/
│   ├── api/               FastAPI gateway (filled in 1.3)
│   ├── runtime/           LangGraph (Sprint 4) — skeleton only
│   ├── rag/               arq workers (Sprint 3) — skeleton only
│   ├── mcp/               MCP servers (Sprint 5) — skeleton only
│   └── web/               Next.js 15 (Sprint 3+) — pnpm skeleton
├── packages/shared/       OpenAPI→TS client (generated in 1.4) — skeleton
├── gateway/litellm/       config.yaml (Sprint 2); present as a compose service in 1.1
├── workflows/             n8n exports (Sprint 6) — empty
├── infra/
│   ├── compose/           docker-compose.dev.yml  ← the main 1.1 deliverable
│   ├── helm/fleet/        umbrella chart (1.5)
│   ├── k3d/               bootstrap scripts (1.5)
│   └── migrations/        alembic (1.2)
├── evals/                 datasets/runner (Sprint 5+) — skeleton
├── tests/                 unit/ integration/ e2e/ load/ security/
├── docs/                  ALREADY EXISTS — not touched (source/ split/ originals)
├── Makefile               all make targets
├── pyproject.toml         uv workspace (Python)
├── pnpm-workspace.yaml    pnpm workspace (JS)
├── .githooks/pre-push     pre-push hook (task 1.0)
└── .github/workflows/     CI (1.2)
```

## Dev Stack — `docker-compose.dev.yml` (11 services)

All images are pinned to a fixed major/minor tag (no `:latest`) so `make dev` is reproducible.

| Service | Image (pinned) | Purpose |
|---|---|---|
| postgres | postgres:16 | primary DB + `fleet_readonly` role |
| redis | redis:7 | cache, rate-limit, arq queue |
| qdrant | qdrant/qdrant | vector DB (RAG) |
| minio | minio/minio | object store (documents) |
| keycloak | keycloak:26 | OIDC/RBAC; realm imported from file |
| litellm | ghcr.io/berriai/litellm | LLM gateway (config in Sprint 2) |
| langfuse | langfuse/langfuse:2 | LLM trace/observability |
| prometheus | prom/prometheus | metrics |
| grafana | grafana/grafana | dashboards; datasources provisioned |
| loki | grafana/loki | log aggregation |
| alertmanager | prom/alertmanager | alerting |
| mailpit | axllent/mailpit | dev SMTP capture |

Keycloak realm is imported from `infra/compose/keycloak/fleet-realm.json` with 5 users
(admin, builder, approver + 2 regular). Grafana provisions Prometheus + Loki datasources
from files under `infra/compose/grafana/`.

## Makefile Targets

Core targets land in Stage A; later ones are added as their stage arrives. Names match
CLAUDE.md Commands.

```
make dev        (A)  docker compose -f infra/compose/docker-compose.dev.yml up -d
make down       (A)  stop the stack
make lint       (A)  uv run ruff + mypy ; pnpm lint (eslint + tsc)
make test       (B)  unit + testcontainers integration
make migrate    (B)  alembic upgrade head
make seed       (B)  synthetic data + analytics fixture views
make scan       (B)  trivy + bandit + gitleaks
make k3d-up     (C)  k3d cluster + helm install
```

## Task 1.0 — Git Bootstrap

- **pre-push hook:** `.githooks/pre-push`, activated with `git config core.hooksPath .githooks`
  and committed to the repo. Runs `make lint` + unit tests; rejects the push if either fails.
- **Commit convention:** already recorded in CLAUDE.md § *Commit & Branch Convention* — single
  sentence English subject, no `Claude`/AI byline, no `Co-Authored-By` trailer. The hook is only
  the technical gate; the human writes the message and runs the commit.
- **Branch protection (GitHub side):** deferred to the end of Stage C, once the 1.2 CI checks
  exist and are green. At that point the user decides whether it is set via `gh` CLI or manually
  in repo Settings → Branches (require a PR, require the CI checks to pass, no direct pushes to
  `main`).

## Verification Flow (per stage)

Follows the Task Execution Protocol (steps 3–7):

1. `make lint && make test` green.
2. **Docker live verification:** bring the stack up with `make dev` and test that stage's ACs
   against the running containers (not mocks).
3. Deliver a findings report: what was built, what was tested and how, per-task AC pass/fail.
4. Append an entry to `docs/PROGRESS.md` (append-only; create on first use).
5. Get user approval, then move to the next stage.
6. **Sprint close** (after Stage C): no `make eval` needed (this sprint ships no agents) → write
   `docs/reports/sprint-1.md` → `/graphify . --update` → prepare the single-sentence English
   commit message and **stop for the user to commit and open/merge the PR** (never run `git commit`
   unless explicitly told).

## Non-Goals (YAGNI)

- No application/business logic inside skeleton app packages — each fills in during its own sprint.
- No `test`/`demo/staging`/`prod` environments stood up here — only `local` (compose) and a local
  k3d cluster. The other three are server-side infrastructure provisioned at release (TRD §14);
  the Helm chart + per-env values are prepared but not deployed.
- No Tempo/Jaeger in the 1.1 stack — dev tracing uses the OTel logging exporter (Tempo/Jaeger is
  a [P2] add-on per the plan).
- No LiteLLM model config — that is Sprint 2; here LiteLLM is only a booting compose service.

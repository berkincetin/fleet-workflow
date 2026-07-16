# Sprint 1 Report — Repo, Stack, CI, Gateway

**Completed:** 2026-07-16 · **Branches/PRs:** Stage A (PR #1), Stage B (PR #2), Stage C (PR #3), close (this).
**Method:** brainstorm → spec → plan → subagent-driven implementation (fresh implementer + task review + fixes per task) → live AC verification → CI green → merge. Durable log in `docs/PROGRESS.md`; per-task detail in the SDD ledgers.

Sprint 1 was delivered in three stages against the plan's tasks 1.0–1.5.

## Tasks & Acceptance Criteria

| Task | What shipped | AC result |
|---|---|---|
| **1.0** Git & GitHub bootstrap | Repo on GitHub; `.githooks/pre-push` (lint+unit, blocks a bad push); commit convention in CLAUDE.md | ✅ pre-push blocks failing pushes (verified live). **Branch protection deferred** — needs GitHub Pro on a private repo; recorded as REQUIRED-before-prod in `docs/PRODUCTION_CHECKLIST.md`. |
| **1.1** Monorepo + dev stack | uv+pnpm workspace; full dir tree; Next.js 15 web skeleton; `docker-compose.dev.yml` (12 services); Makefile; Keycloak realm; Grafana/Prometheus/Loki provisioning | ✅ `make dev` booted all 12 services; Keycloak `fleet` realm imported with 5 users; Grafana had Prometheus+Loki datasources — all verified live. |
| **1.2** CI + migrations + seed | GitHub Actions PR pipeline (lint→unit→integration→security→build-image); Alembic + first migration (departments/users/roles/audit_log + `fleet_readonly`); idempotent seed + analytics fixture views | ✅ **All 5 CI jobs green on GitHub** incl. integration actually starting testcontainers (not skipped); migration + seed verified against real Postgres. |
| **1.3** Gateway auth core | `create_app` factory; config; error model; `/healthz`+`/readyz`; OIDC RS256 validation vs Keycloak JWKS; RBAC permission service (§7.1 roles) | ✅ integration tests cover 401 (no token), 401 (bad token), 200 (member/CHAT), 403 (member lacks MANAGE_PLATFORM) against a real Keycloak — green locally and in CI. |
| **1.4** Cross-cutting middleware | trace_id + `X-Trace-Id`; append-only audit carrying trace_id (actor from verified token sub); Redis rate limiter (429); OTel console exporter; OpenAPI→TS client in `packages/shared` | ✅ audit row carries the request trace_id; rate limit returns 429; verified against real Postgres+Redis. TS client generated + typechecks. |
| **1.5** Helm umbrella chart + k3d | `infra/helm/fleet` (8 service templates, values + values-dev); `infra/k3d` bootstrap; Makefile k3d targets | ✅ `make k3d-up` (up.sh) brought up the stack on a real k3d cluster — **8/8 service pods Running** (verified twice). |

## What was tested and how

- **Unit** (`make test` → `pytest tests/unit`): health endpoint, ORM metadata, app-factory smoke — run with no backends (via `create_app(with_middleware=False)`).
- **Integration** (`pytest tests/integration`, testcontainers): migration applies + `fleet_readonly` created (Postgres); seed populates + fixture views (Postgres); OIDC/RBAC 401/401/200/403 (real Keycloak 26 + Postgres + Redis); audit-row-has-trace_id and rate-limit-429 (Postgres + Redis). 8 integration tests total.
- **Docker/live:** `make dev` (12-service compose) for 1.1 ACs; `make k3d-up` (k3d cluster) for 1.5 — pods reached Running, checked with `kubectl get pods`.
- **CI (GitHub Actions):** the full 5-job pipeline ran green on PR #2 and PR #3, including the testcontainers integration job and a trivy image scan.
- **Security scans:** bandit + gitleaks (CI), trivy on the built image (clean, no HIGH/CRITICAL).

## Notable issues resolved (symptom → root cause → fix)

- **Windows tooling:** `make`/`uv`/`helm`/`k3d`/`kubectl`/`gh` not installed or not on the Git-bash PATH → installed via winget; Makefile made cross-platform (`-` prefix instead of shell `||true`); pre-push hook calls tools directly (Git bash can't see Windows-only `make`).
- **ESLint 9 + Next 15:** `next lint` failed (RushStack patch) → switched to the FlatCompat pattern.
- **CI action versions:** gitleaks needed `GITHUB_TOKEN` + `pull-requests:read`; trivy-action tag/setup was flaky → scan with the official `aquasec/trivy` image via the docker socket.
- **Auth security:** Keycloak 26 omits `aud` (uses `azp`) — verified this is safe (signature+issuer still enforced, `none` alg impossible). Audit `actor` was client-controlled (`X-User`) → now derived from the verified token `sub`.
- **Middleware discipline (CLAUDE.md rule 6):** a subagent had added `except: pass` swallowing audit/rate-limit failures → removed; audit is a hard guarantee; test isolation fixed with real backends.
- **create_app + middleware:** unit test then needed Redis/Postgres → added `with_middleware` flag (prod default on).
- **k3d on Docker Desktop:** kubeconfig written as `host.docker.internal` didn't resolve to the published loopback → `up.sh` pins the server to `127.0.0.1:<mapped-port>`.
- **Keycloak in CI:** host-temp-dir realm mount worked locally but not on GitHub runners → provision the realm via the Keycloak Admin REST API (no host mount); user renamed `m`→`member` (26 rejects <3-char usernames).

## Deviations / deferrals

- Plan prose said "11-service stack"; the correct stack is 12 (incl. mailpit) — a plan label off-by-one, implementation is right.
- Branch protection deferred to production (see above; `docs/PRODUCTION_CHECKLIST.md`).
- Forward hardening (recorded, non-blocking): JWKS caching; a shared `app.state` engine (audit + `/readyz` open per-request engines today); `env.py` URL duplication; NetworkPolicies in the Helm chart (Sprint 9 hardening); `packages/shared` carries both a `pyproject.toml` and `package.json`.

## State at sprint end

The platform boots locally (compose + k3d), authenticates and enforces RBAC, propagates trace_id, writes an append-only audit trail, rate-limits, and ships a green CI pipeline that gates every PR. This is the foundation Sprint 2 (LLM gateway + budgets) builds on. No new business logic beyond the gateway skeleton — by design.

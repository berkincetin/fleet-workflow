# Implementation Plan · Sprint 1 — Repo, Stack, CI, Gateway

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 1 — Repo, Stack, CI, Gateway

- **1.0 Git & GitHub bootstrap.** `git init` this repo; create the GitHub remote; push `main`; enable branch protection on `main` (require the CI checks from 1.2 to pass and require a PR — no direct pushes to `main`). Add a `pre-push` git hook that runs `make lint` + unit tests locally so obviously-broken work never reaches a PR. Record the commit convention (see CLAUDE.md § *Commit & Branch Convention*): single-sentence English subject, **no** `Claude`/AI attribution and **no** `Co-Authored-By` trailer. *(User creates the GitHub repo + grants push access at this step — per the Task Execution Protocol.)*
  **AC:** `main` is protected (a direct push is rejected; a PR is required); an opened PR runs the 1.2 CI checks and cannot be merged until they are green; the `pre-push` hook blocks a push when unit tests fail.
- **1.1 Monorepo + dev stack.** Layout per CLAUDE.md; `docker-compose.dev.yml` (postgres, redis, qdrant, minio, keycloak, litellm, langfuse, **prometheus, grafana, loki, alertmanager, mailpit**); Makefile targets; bootstrap README (dev setup — finalized in 10.1). The four environments (`local` compose, `test`, `demo/staging`, `prod` — TRD §14) share one Helm chart with per-env values; only `local` is stood up here, the other three are provisioned as infrastructure later (1.5 chart, deployed to servers at release).
  **AC:** `make dev` boots the full stack (incl. mailpit); Keycloak realm imported from file (fleet realm, 5 test users incl. admin/builder/approver); Grafana reachable with Prometheus + Loki datasources provisioned.
- **1.2 CI + migrations + seed.** GitHub Actions **matching TRD §14 PR pipeline**: lint+typecheck → unit → **integration (testcontainers: Postgres/Redis/Qdrant/MinIO)** → security scans (trivy, bandit, gitleaks) → build+scan images, on every PR; alembic init + first migration (users, departments, roles, audit_log); seed script with synthetic data, **including the analytics fixture warehouse views** consumed by 5.2's evals. Integration tests run in CI via Docker-in-the-runner (testcontainers); this is the CI half of the "unit + docker integration on every change" rule.
  **AC:** `make test` (unit **and** testcontainers integration) runs a passing suite in CI; the integration job actually starts containers (not skipped); security jobs pass (no high severity); image build+scan job passes; `make seed` loads demo data incl. fixture views.
- **1.3 Gateway auth core.** FastAPI app factory; OIDC token validation; RBAC decorator + permission service; error model; health/readiness endpoints.
  **AC:** integration tests cover 401/403 paths.
- **1.4 Gateway cross-cutting middleware.** Audit middleware (append-only writes); OpenTelemetry wiring (trace_id in/out); Redis rate limiter; OpenAPI → generated TS client in `packages/shared`.
  **AC:** audit row written with trace_id; rate limit 429 test; traces exported and inspectable (OpenTelemetry logging exporter in dev; Tempo/Jaeger is a [P2] add-on — not part of the 1.1 stack).
- **1.5 Helm umbrella chart skeleton + k3d bootstrap.** `infra/helm/fleet` umbrella chart covering the 1.1 stack; `infra/k3d` bootstrap scripts; `values-dev.yaml`. From here on, every new service adds its chart entry + resources + NetworkPolicy in the same PR (CLAUDE.md convention).
  **AC:** `make k3d-up` brings up the 1.1 stack on a local k3d cluster from the chart.

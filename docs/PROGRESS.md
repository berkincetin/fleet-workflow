# PROGRESS — Fleet Platform

Durable, append-only status log (Task Execution Protocol step 6). Never edit past entries.

## 2026-07-15 — 1.0 (git hook + convention) + 1.1 (monorepo + dev stack) — DONE

Built (Stage A of Sprint 1, branch `feat/sprint-1-stage-a`):
- uv + pnpm monorepo workspace root (pyproject.toml, ruff/mypy config, pnpm-workspace, .gitignore).
- Full repo directory tree (apps/{api,runtime,rag,mcp,web}, packages/shared, gateway, workflows, infra, evals, tests) as skeletons.
- Next.js 15 + TS web skeleton under apps/web (builds + lints clean).
- .env.example + Keycloak `fleet` realm (5 users) + observability provisioning (Prometheus/Grafana/Loki/Alertmanager).
- infra/compose/docker-compose.dev.yml — 12-service local dev stack, pinned image tags.
- Makefile (dev/down/lint/test) + task-1.0 pre-push hook (`.githooks/pre-push`) + smoke test.

Verified (live, against real containers):
- `make lint` exit 0; `make test` → 1 passed (PowerShell + make).
- pre-push hook exits 0 on clean tree, exits 1 (blocks push) on a bad file (Git bash).
- `make dev` booted all 12 services (postgres/redis/minio/mailpit healthy; rest running).
- AC 1.1: Keycloak `fleet` realm imported with exactly 5 users (admin/builder/approver/user1/user2) — verified via admin API.
- AC 1.1: Grafana provisioned datasources — Prometheus (default, http://prometheus:9090) + Loki (http://loki:3100) — verified via Grafana API.
- AC 1.1: mailpit UI reachable (HTTP 200). `make down` tore the stack down cleanly.

Issues (symptom → root cause → resolution; solved issues logged too):
- Task 3: `next lint` exit 1 → eslint-config-next@15.1.0 + ESLint 9 flat-config RushStack patch bug → switched to the official FlatCompat pattern (`eslint .`, added @eslint/eslintrc@3.2.0); eslint 9 kept. RESOLVED.
- Task 3: next-env.d.ts got committed → no apps/web/.gitignore existed → added apps/web/.gitignore, untracked it. RESOLVED.
- Task 7: `make lint` failed on `... || true` → make runs recipes via cmd.exe on Windows (no `true`) → replaced with make's `-` line-prefix. RESOLVED.
- Task 7: pre-push hook failed under Git bash → hook called Windows-only `make`, and Git's bundled bash couldn't see it (also picked an older uv) → rewrote hook to call tools directly + prepend $HOME/.local/bin. RESOLVED.
- Windows prerequisite: `make` and `uv` were not installed → installed both via winget (make 4.4.1, uv). RESOLVED.

Notes / deviations:
- Plan prose said "11-service stack"; the real (correct) stack is 12 services incl. mailpit — plan label off-by-one; implementation is right. Fix the label in the plan/docs later.
- Task 2 added minimal pyproject.toml per Python workspace member (uv requires it); the uv glob was later narrowed to explicit Python apps + `exclude apps/web` (design decision with the user).
- Task 3 tsconfig.json carries 4 standard create-next-app compilerOptions beyond the brief (Next 15 build relies on them) — brief was incomplete, kept the correct tsconfig.
- Branch protection (the GitHub side of task 1.0) is deliberately deferred to the end of Stage C (after the 1.2 CI checks exist). Not done here.
- Meta on this repo: commits are made automatically here (user's decision 2026-07-15); still land via feature branch + PR, never a direct push to protected main.

## 2026-07-15 — 1.2 (CI + migrations + seed) — DONE

Built (Stage B of Sprint 1, branch `feat/sprint-1-stage-b`, PR #2):
- Async DB layer + ORM models (`apps/api/fleet_api/{db,models}.py`): Department, User, Role, AuditLog.
- Alembic (`infra/migrations/`) + first migration `0001_initial` (4 core tables + read-only `fleet_readonly` role).
- Idempotent seed (`fleet_api/seed.py`): synthetic departments/users + analytics fixture views (fixture_sales 500 rows, fixture_orders) granted SELECT to fleet_readonly (for 5.2 evals).
- Makefile: `test` now unit+integration; added `migrate`, `seed`, `scan`. pytest.ini (asyncio auto + integration marker).
- Minimal `apps/api/Dockerfile` (pinned python:3.12-slim + uv 0.7.12, non-root) + repo-root `.dockerignore`.
- GitHub Actions `.github/workflows/ci.yml`: lint → unit → integration(testcontainers) → security(bandit+gitleaks) → build-image(build + trivy scan).
- Langfuse isolated onto its own `langfuse` DB via a postgres init script.

Verified (live):
- Locally: `make migrate`/`make seed` against compose Postgres; `make test` = 2 unit + 2 integration pass; docker image builds + runs; trivy scans clean (0 HIGH/CRITICAL).
- **On GitHub (PR #2, run 29433998276): ALL 5 CI JOBS GREEN** — lint, unit, integration (testcontainers actually starts postgres:16, NOT skipped), security, build-image. This is the real 1.2 AC.

Issues (symptom → root cause → resolution):
- bandit missing from deps → security job would fail "command not found" → added bandit>=1.7 to dev-deps (caught in review pre-run). RESOLVED.
- gitleaks "GITHUB_TOKEN required" then "Resource not accessible by integration" 403 → gitleaks-action breaking change + insufficient perms → added GITHUB_TOKEN env + `permissions: pull-requests: read`. RESOLVED.
- trivy-action@0.28.0 "unable to find version" → wrong tag (tags are v-prefixed); bumping to v0.33.1 then hit flaky setup-trivy binary download (exit 1) → replaced trivy-action with `docker run aquasec/trivy:0.65.0` scanning the built image via docker socket. RESOLVED.
- Langfuse pointed at a `langfuse` DB that didn't exist (out-of-scope change in B4) → added postgres init script to CREATE DATABASE langfuse; verified Langfuse boots + isolates its 42 tables. RESOLVED.

Notes / deviations:
- Root pyproject now depends on `fleet-api` (+[tool.uv.sources]) so the member installs editable for tests/CI. Same pattern will be needed for runtime/rag/mcp/shared later.
- asyncpg rejects multi-statement prepared statements → seed splits the two CREATE VIEW calls; view bodies unchanged, still atomic.
- postgres init scripts only run on a FRESH pgdata volume — a pre-existing dev volume needs `docker compose down -v` once to get the langfuse DB.

## 2026-07-16 — 1.3 (auth core) + 1.4 (middleware) + 1.5 (Helm/k3d) — DONE

Built (Stage C of Sprint 1, branch `feat/sprint-1-stage-c`):
- **1.3 auth core:** `create_app` factory (`app.py`), config (`config.py`, FLEET_ env), domain error model (`errors.py`, AppError/401/403), health/readiness (`/healthz`, `/readyz`), OIDC RS256 token validation vs Keycloak JWKS (`auth.py`), RBAC permission service enforcing TRD §7.1 (`rbac.py`, roles platform_admin/dept_admin/builder/approver/member), protected demo routes (`whoami.py`).
- **1.4 middleware:** trace_id per request + X-Trace-Id header (`middleware.py` TraceIdMiddleware), append-only audit carrying trace_id (AuditMiddleware + `audit.py`), Redis fixed-window rate limiter → 429 (RateLimitMiddleware), OTel console span exporter (`otel.py`). OpenAPI → generated TS client in `packages/shared` (@fleet/shared, openapi.json + schema.d.ts).
- **1.5:** Helm umbrella chart `infra/helm/fleet` (8 service templates, values + values-dev), k3d bootstrap (`infra/k3d/{cluster.yaml,up.sh}`), Makefile helm-lint/k3d-up/k3d-down.

Verified (live):
- AC 1.3: 401 (no token), 401 (bad token), 200 (member with CHAT), 403 (member lacks MANAGE_PLATFORM) — all pass against a REAL Keycloak 26 testcontainer.
- AC 1.4: an audit_log row is written with the request's trace_id (asserted equal to X-Trace-Id header); rate limiter returns 429 past the limit — against real Postgres + Redis testcontainers.
- AC 1.5: `make k3d-up` (up.sh) creates a k3d cluster and helm-installs the chart; **8/8 service pods reach Running** (postgres/redis/qdrant/minio/keycloak/prometheus/grafana/loki). Verified twice.
- Full gate: `make lint` green; unit (3, no backend) + integration (8, real containers) all pass.

Issues (symptom → root cause → resolution):
- OIDC 200 case risk: Keycloak 26 tokens omit `aud` (use `azp`) → python-jose verify_aud=True means "match if present"; signature (RS256 vs JWKS) + issuer verified unconditionally → safe, verification NOT weakened (reviewer confirmed from library source). RESOLVED.
- Middleware silently swallowed audit/rate-limit errors (implementer added `except: pass`, violating CLAUDE.md rule 6) to mask that the auth test built the app without Postgres/Redis → removed both excepts (audit = hard guarantee); gave test_auth_rbac.py real Postgres+Redis backing. RESOLVED.
- create_app unconditionally wired middleware → unit test_health then needed Redis/Postgres → added `with_middleware` flag (default True); unit tests build with it False. RESOLVED.
- `make k3d-up` kubectl couldn't reach the cluster: k3d wrote kubeconfig as host.docker.internal, which on Windows/Docker Desktop didn't resolve to the published loopback port → up.sh now pins the kubeconfig server to 127.0.0.1:<mapped-port>. RESOLVED.

Notes / deviations:
- Branch protection (GitHub side of task 1.0) is enabled by the controller right after this PR merges (it needs the CI checks to exist and be green first). Sprint 1 close (sprint report + graph refresh) follows.
- helm/k3d/kubectl were installed via winget this session; on this machine they + `make` are not all on the Git-bash PATH simultaneously (same class as the Stage-A make/uv PATH note) — `make k3d-up` works when they share a PATH.
- Forward (non-blocking): JWKS has no caching (fetch per request); `/readyz` opens a fresh engine per call; env.py URL-build duplicates db.py; NetworkPolicies not in the chart yet (Sprint 9 hardening). All recorded in the SDD ledger.

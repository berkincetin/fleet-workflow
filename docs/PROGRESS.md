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

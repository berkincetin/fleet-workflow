# TRD · Environments, CI/CD, Backup (§14)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 14. Environments, CI/CD, Backup

- **Environments (4):** `local` (dev machine, compose — the only one built during development) → `test` (CI/integration target) → `demo/staging` (k3d/Helm on a server) → `prod` (any K8s, same chart, values-per-env). One umbrella chart with per-env values covers all four: api, web, runtime-workers, rag-workers, mcp-*, litellm, langfuse, n8n(main+workers), keycloak, postgres (CloudNativePG), redis, qdrant, minio, kube-prometheus-stack, loki. `make k3d-up` = full local cluster in ~10 min. The `test`, `demo/staging`, and `prod` environments are provisioned as **infrastructure** (chart + values ready from Sprint 1.5) and stood up on their servers only at release time — development happens entirely against `local`.
- **CI/CD (GitHub Actions):**
  - **`main` is branch-protected:** direct pushes are rejected; changes land via PR, and a PR can only merge once the required checks pass (this is how "no commit ships without passing CI" is enforced — GitHub Actions gates the *merge*, not the local commit; a local `pre-push` hook additionally runs lint+unit before a push). Commit convention: single-sentence English subject, no AI attribution, no `Co-Authored-By` trailer.
  - **PR pipeline:** lint+typecheck → unit → **integration (testcontainers: Postgres/Redis/Qdrant/MinIO)** → security (trivy/bandit/gitleaks) → affected-agent evals → build+scan images. GPU-dependent local-lane evals are marked and run on a self-hosted GPU runner (or nightly), never gating hosted-runner PRs.
  - **Release/deploy:** merge to `main` → deploy `demo/staging` → E2E+k6 smoke → manual gate → `prod`. A **version tag** (`v*`) triggers the release pipeline (full check suite + release image build). Migrations via Alembic job pre-deploy.
- **Backup/DR [CORE]:** Postgres PITR (WAL to MinIO, CloudNativePG scheduled backups), Qdrant snapshots nightly→MinIO, MinIO versioning; restore runbook in `docs/runbooks/`; RPO 24h / RTO 4h (internal tool tier).

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

## 2026-07-21 — 2.1 LiteLLM + 2.2 registry + 2.3 gateway client + 2.4 budgets — DONE

Built (Sprint 2, branch `feat/sprint-2-gateway-budgets`):
- **2.1 LiteLLM proxy:** `gateway/litellm/config.yaml` — Day-0 pinned model matrix (9 models, TRD §4.2: reasoning/utility/embeddings + fallbacks + local qwen2.5/bge-m3), per-model fallback chains, Langfuse success/failure callback. `gateway/litellm/pricing_sync.py` (pure `sync_prices` + `--check` CLI). Wired config into the compose litellm service (mount + `--config` + provider/Langfuse env). Makefile `gateway-sync`/`gateway-check`.
- **2.2 model registry:** `models` table (ORM `Model` + migration `0002_models`, §4.1 schema). `fleet_api/registry.py` (pure `build_model_row` + `evaluate_smoke`, enforces "no cloud model cleared for pii"), `registry_probe.py` (live smoke probe through the proxy), `routers/models_admin.py` (`/v1/admin/models` CRUD gated by MANAGE_PLATFORM, add→smoke→store). `get_session` dep added to db.py. Default matrix seeded in seed.py.
- **2.3 gateway client (`apps/runtime/core/llm/`):** the ONLY LLM call site (rule 1). `routing.py` (Sensitivity IntEnum, effective-sensitivity + §8 redaction-downgrade, `select_model` refusal), `cost.py` (usage parse + cost w/ cached price), `client.py` (`reasoning()`/`utility()`, sensitivity enforced before transport, spend recorded, GatewayError on exhausted fallback), `transport.py` (httpx→proxy, no provider SDK), `ledger.py` (spend_ledger sink), `factory.py` (build_client from registry). Made `apps/runtime` an installable `fleet-runtime` workspace member.
- **2.4 budgets:** `budgets` + `spend_ledger` tables (migration `0003`, §11 schema). `budget.py` (pure `evaluate_budget` 80/100 + `DbBudgetChecker` over global→dept→agent→user hierarchy). Integrated into the client: hard-stop raises `BudgetExceeded` before transport, soft flag surfaced on `LLMResponse.budget_soft_exceeded`.

Verified (unit + live against the compose stack):
- Unit: **62 passed** — sensitivity routing (9, incl. redaction downgrade + pii refusal), cost (5), client orchestration (6), client+budget (4), budget decision (9), registry (6), pricing sync (5), litellm config (6), factory (3), + Sprint 1.
- Integration: **13 passed** (real containers) incl. 5 new — spend_ledger sink write + budget pre-check hard-stop/unlimited (Postgres testcontainer), smoke-test-on-add active/error against the LIVE proxy.
- **AC 2.1:** proxy booted from `/app/config.yaml`, `GET /v1/models` returned all 9 pinned models. `pricing_sync --check` → "pricing in sync" exit 0.
- **AC 2.2:** live probe of `utility` → reachable → row `active`/`ok` w/ latency; unknown model → `error`/`failed`.
- **AC 2.3:** live **cloud** call via client → served gpt-4o-mini, spend_ledger row (12/1 tok, $0.0000012); live **Ollama** call w/ sensitivity=pii → routed to `ollama/qwen2.5:7b-instruct-q4_K_M`, spend row (43/2 tok, $0.00). **Langfuse** recorded traces for gpt-4o-mini + gemini-1.5-flash + qwen2.5 (observations w/ token usage). Fallback chain proven live (see Issues).
- **AC 2.4:** unit hard-stop blocks call + bills nothing; soft-limit sets `budget_soft_exceeded` on the response; DB pre-check hard-stops when period spend > limit.
- Full gate: `make lint` exit 0 (ruff clean, web eslint clean, mypy advisory), `make test` exit 0.

Issues (symptom → root cause → resolution; solved logged too):
- **SECURITY:** real ANTHROPIC/OPENAI/GEMINI keys were pasted by the user into `.env.example` (git-TRACKED) → would leak on push → moved them to `.env` (gitignored), reset `.env.example` to empty placeholders. Keys were on disk in a tracked file but never committed. **Flagged to user to rotate.** RESOLVED (rotation is the user's call).
- Gemini key **invalid** (`API_KEY_INVALID` from googleapis) and Anthropic key failing → `utility`(Gemini)→gpt-4o-mini and `reasoning`(Claude)→gpt-4o via the fallback chain. User pre-warned keys may be exhausted. NOT a code defect — the fallback + graceful-degradation (§4.4) worked exactly as designed; OpenAI served all calls. Left as-is (env/key issue, per protocol rule 5 not a code fix).
- Proxy's Langfuse callback logged "disabled, no public_key" on first boot → keys were empty → added Langfuse **headless-init** env (fixed dev keypair) to the langfuse compose service + matching defaults on litellm; force-recreated both → callback active, traces land. RESOLVED.
- First qwen2.5 call via proxy returned empty/non-JSON → cold-start model load latency on a freshly-pulled 7B → warmed the model directly on Ollama, then the client call succeeded. RESOLVED (expected first-load behavior).
- ruff ASYNC109 on `probe_model(timeout=…)` → httpx owns the timeout → scoped `# noqa` with rationale. Import-order nits in two test files → `ruff --fix`. RESOLVED.
- **CI `security` job failed on PR #5:** bandit B608 (Medium/Low-confidence) on `budget.py`'s f-string-built spend query → the interpolated `{column}` was never user input (a fixed lookup dict, unreachable scope_types raise first), but the *pattern* still trips bandit's SQL-injection heuristic → replaced the single f-string branch with three literal per-scope SQL strings (dept/agent/user), no interpolation at all; removed the now-unused `_SCOPE_COLUMN` dict. Reported root cause + 3 options to the user before touching code (rule 5); user picked the literal-queries fix. Verified: `bandit -r apps packages -ll` → 0 issues; ruff/mypy clean; unit+integration green; **all 10 CI checks pass on PR #5** (lint/unit/security/integration/build-image × 2 runs). RESOLVED.

Notes / deviations:
- `models` registry (§4.1) has no `fleet_role` column — TRD treats roles as per-agent model references. The factory derives a tier role from the default-matrix model name (`derive_role`) so `reasoning()`/`utility()` can route; documented in factory.py. A future per-agent `reasoning_model`/`utility_model` (agents table, §11) will supersede this.
- Budget admin CRUD UI is task 7.1, not 2.4 — 2.4 delivered the table + pure decision + async pre-check + client integration only.
- The user pulled `qwen2.5:7b-instruct-q4_K_M` (~4.7GB) this session so the pinned local model matches the config; `llama3.2-vision` was already present.
- Langfuse init keys `pk-lf-fleet-dev`/`sk-lf-fleet-dev` are dev-only defaults baked into compose for out-of-the-box tracing; override in `.env` for a real project.
- mypy still advisory (11 pre-existing errors in Sprint-1 auth/middleware/rbac; zero in the 10 new Sprint-2 modules).

## 2026-07-21 — 3.1 ingestion pipeline + 3.2 collections/retention — DONE

Built (Sprint 3, branch `feat/sprint-3-rag`):
- **`collections`/`documents`/`chunks` tables** (migration `0004_rag_collections`, ORM `Collection`/`Document`/`Chunk`, TRD §8/§11 schema) — unique `(collection_id, sha256)` on documents (dedup-by-sha) and unique `qdrant_point_id` on chunks.
- **New `fleet-rag` workspace package** (`apps/rag/fleet_rag/`): `ingest/extract.py` (pdf/docx/txt, flags `needs_ocr` for scanned PDFs/images), `ingest/ocr.py` (vision-LLM primary via the governed `LLMClient`, tesseract `tur+eng` fallback, injected so no local tesseract binary is needed for tests), `ingest/pii.py` (Presidio + custom TR recognizers — TCKN checksum, TR IBAN, TR phone — plus `redact`/`block`/`allow-local-only` policy application per TRD §8), `ingest/chunk.py` (paragraph-packed chunking + content-sha256 dedup), `ingest/pipeline.py` (pure `run_ingestion` orchestrating extract→OCR→PII→chunk→dedup→embed→Qdrant-upsert, all I/O injected), `ingest/worker.py` (arq `WorkerSettings` + `ingest_document` task wiring the real MinIO/LLMClient/Qdrant/Postgres), `ingest/retention.py` (`is_expired` pure predicate + `purge_expired` orchestration + `purge_expired_cron` registered as a nightly 03:00 arq cron job), `store/minio_store.py`, `store/qdrant_store.py` (deterministic point IDs via `uuid5` of the content hash so re-embedding upserts in place).
- **Gateway client extended for embeddings** (Sprint 2's `apps/runtime/core/llm/`): `LLMClient.embeddings()` + `EmbeddingResponse`, `ProxyTransport.embed()` (`/embeddings`) — same sensitivity-routing/budget/spend-ledger pipeline as `reasoning()`/`utility()`, so `pii` sensitivity correctly refuses cloud and routes to `local-embeddings` (Ollama bge-m3).
- **`apps/api` additions:** `routers/documents.py` (`POST/GET /v1/documents` — content-addressed MinIO upload, re-upload resolves to the existing row idempotently, enqueues the `ingest_document` arq job; UPLOAD permission), `routers/collections.py` (full CRUD on `/v1/collections`, MANAGE_DEPT for writes, validates sensitivity/pii_policy enums and rejects `pii`+`redact` — redact would downgrade pii routing, which §8 forbids). `fleet-api` gained `arq`/`minio`/`python-multipart` deps (kept `fleet_rag` import out of `fleet-api` to avoid a circular workspace dependency — small hash/key helpers duplicated instead).

Verified (unit + live against the compose stack, incl. real Ollama bge-m3 pulled this session):
- Unit: **113 passed** — chunk (7), extract (5), ocr (4), pii incl. TCKN checksum (11), pipeline orchestration (6), minio/qdrant store helpers (7), retention predicate + purge orchestration w/ fakes (7), gateway client embeddings (3 new) + Sprint 1/2 carry-forward.
- Integration: **19 passed** (real containers) incl. 6 new — MinIO/Qdrant live roundtrip, full upload→arq-ingest→Qdrant pipeline via the real LiteLLM proxy (OpenAI `text-embedding-3-small`), retention purge deleting a real chunk/document/MinIO-object/Qdrant-point, PII/`allow-local-only` collection routing to the local Ollama bge-m3 lane, collections list endpoint.
- **AC 3.1:** live upload of a `.txt` doc → arq job (run both inline in a test AND via a real `arq ... --burst` CLI process against live Redis) → 1 chunk embedded, document `status=ready`, chunk found in Qdrant. Re-upload of byte-identical content → same `document_id` returned, **0 new embed calls** (verified via the dedup unique index + a pipeline unit test asserting `chunks_embedded=0`/`llm.embed_calls==[]` on full-cache).
- **AC 3.2:** PII doc (`sensitivity=pii`, `pii_policy=allow-local-only`) ingested end-to-end → embedding call routed to `local-embeddings`/Ollama bge-m3 (never cloud), chunk landed in Qdrant with `redacted=False` (allow-local-only keeps text intact, unlike redact) — proves the local-lane routing rule live, not just via the Sprint-2 routing unit tests. Retention purge: real chunk row, document row, MinIO object, and Qdrant vector all confirmed deleted for a document past its collection's `retention_days`; object-store failure (already-deleted file) does not abort row deletion.
- Full gate: `ruff check .` clean, `mypy apps` → same 12 pre-existing Sprint-1 errors (0 new), `pytest tests/unit` 113/113, `pytest tests/integration` 19/19.

Issues (symptom → root cause → resolution; solved logged too):
- Docker Desktop wasn't running at session start → user started it, stack (`make dev`) brought up cleanly (Postgres/Redis/MinIO/Qdrant all healthy). RESOLVED.
- `presidio_analyzer.AnalyzerEngine()`'s default config auto-downloads `en_core_web_lg` via spaCy's pip-based CLI downloader → uv-managed venvs have no `pip` module → hung/failed silently (`No module named pip` on stderr, engine construction never completed). Fixed by explicitly configuring `NlpEngineProvider` with the smaller `en_core_web_sm` model, vendored as a direct-URL `uv add` dependency (`apps/rag/pyproject.toml`) so it's present without a runtime download. RESOLVED.
- `qdrant-client` resolved to 1.18.0 vs the compose-pinned server 1.12.4 → version-mismatch warning on every call → pinned `qdrant-client>=1.12,<1.13` to match. RESOLVED.
- Windows `ProactorEventLoop` + SQLAlchemy's cached asyncpg connection pool (`fleet_api.db._app_session_factory`, an `lru_cache` singleton) do not tolerate being reused across separate `asyncio.run()` cycles / Starlette `TestClient`'s per-call event loop churn → `RuntimeError: Event loop is closed` / `AttributeError: 'NoneType' object has no attribute 'send'` on a second live-integration test run in the same pytest session. Fixed by (a) switching all new live tests from sync `TestClient` to `httpx.ASGITransport` inside a single `asyncio.run()` block per test, and (b) calling `fleet_api.db._app_session_factory.cache_clear()` at the start of each test's async body to force a fresh engine bound to the current loop. Windows/TestClient-specific; production runs under uvicorn's single long-lived loop and is unaffected. RESOLVED.
- Live retention-purge test reused a fixed collection name across repeated runs → the `documents` unique `(collection_id, sha256)` index resolved re-runs to a stale `ready` row from a prior run instead of a fresh `queued` one → switched the fixture to a UUID-suffixed collection name per run. RESOLVED (test-isolation fix, not a product bug).
- bge-m3 (local embedding model) wasn't pulled in Ollama → asked the user before a multi-GB download (per protocol, blocking dependency); user chose to pull it for full live verification of the pii/local-lane AC rather than relying on unit-test coverage alone. RESOLVED.

Notes / deviations:
- Collections API writes require `MANAGE_DEPT`, but no seeded dev-realm Keycloak user currently holds a role matching `rbac.py`'s exact `dept_admin`/`platform_admin` strings (the realm seeds `admin`/`builder`/`approver`/`user`) — a pre-existing Sprint-1/2 gap between the realm JSON and `rbac.py`'s `ROLE_PERMISSIONS` keys, not introduced or fixed here. Live collection creation in tests goes through direct SQL; only the `GET` (UPLOAD-gated, reachable via `builder`) is exercised through the real API. Flagging for a future task since it also blocks `MANAGE_PLATFORM`-gated live testing (Sprint 2's `models_admin` router has the same exposure).
- Retention purge is registered as an arq cron job (`purge_expired_cron`, daily 03:00) but has no manual-trigger admin endpoint — matches the task wording ("retention purge job"); an admin trigger, if wanted, is Sprint 7 (admin/observability) territory.
- `chunks.tokens` is currently a whitespace-split word count (matches `chunk.py`'s own chunking budget metric), not a model-specific tokenizer count — consistent with the approximation already used for chunk sizing; revisit if a precise token accounting becomes load-bearing (e.g. billing).
- The Collections API's `pii`+`redact` rejection is a deliberate product guard beyond the literal task text: TRD §8 defines the redaction-downgrade rule as taking effect only for `confidential`, and allowing a `pii` collection to declare policy `redact` would silently create documents whose *stated* sensitivity is `pii` but whose *effective* routing sensitivity drops to `internal` — the exact bypass CLAUDE.md rule 2 exists to prevent. Enforced at collection-creation time so it can never be configured, not just handled correctly by the pipeline.

## 2026-07-21 — 3.3 query + citations — DONE

Built (Sprint 3, branch `feat/sprint-3-rag`):
- **Gateway client gained `embeddings()`/`EmbeddingResponse`** (extends Sprint 2's `core/llm/client.py` + `transport.py`'s `ProxyTransport.embed()` hitting `/embeddings`) — same sensitivity-routing/budget/spend-ledger pipeline as `reasoning()`/`utility()`; needed by both ingestion (3.1) and query.
- **`fleet_rag/query/retrieve.py`:** pure `retrieve()` — dense kNN via an injected `Searcher`, optional keyword narrowing, and the two §5 context budgets: per-chunk token cap (truncates over-long chunks) and total-retrieved-tokens cap (drops lowest-scoring chunks once spent, results already score-sorted).
- **`fleet_rag/store/qdrant_store.py` extended:** `search_hybrid()` (dense query + optional `MatchText` full-text filter on `content` — the literal "dense + keyword filter" hybrid mode from the task text, not sparse-vector BM25 fusion) and a full-text payload index created alongside each collection in `ensure_collection()`.
- **`fleet_rag/query/answer.py`:** pure `build_answer()` — the TRD §9 structural grounding guardrail. Every answer must carry ≥1 citation and every citation must resolve to a chunk actually retrieved that run; citations are 1-indexed positions into the retrieved-hits list (so the LLM's `[chunk:N]` markers stay short regardless of the chunk's real identifier). A first ungrounded attempt is regenerated once; a second failure degrades to a fixed "I don't know" response, never surfacing an unverifiable claim.
- **`fleet_rag/query/service.py`:** `answer_query()` orchestrates embed(question) → retrieve (hybrid, per-agent `AgentQueryConfig` top_k/token caps) → generate. Retrieved content is wrapped in an `<untrusted_context>` block (CLAUDE.md rule 4) with an explicit instruction to ignore embedded commands, never concatenated raw into the prompt.
- **`apps/api/fleet_api/routers/rag_query.py`:** `POST /v1/rag/query` — the chat-less test-harness endpoint (collection_id, question, top_k, optional keyword) → grounded `{answer, citations, degraded}`. UPLOAD-gated. Registered in `app.py`.
- **`chunks` Qdrant payload gained `content_sha256`** (pipeline.py) so retrieval/citations have a stable chunk identifier without needing the DB-assigned `chunks.id` (not known at Qdrant-upsert time, since the row insert happens after the vector upsert in the current worker ordering) — `Hit.chunk_ref`/`Citation.chunk_ref` carry this sha instead of an integer PK.

Verified (unit + live against the compose stack, incl. real gpt-4o/gpt-4o-mini generation and text-embedding-3-small via the live LiteLLM proxy):
- Unit: **126 passed** — retrieve/context-budgeting (4), citation grounding guardrail incl. regenerate-once/degrade (5), query orchestration wiring (4), gateway client embeddings (3), qdrant/minio store additions, + full Sprint 1–3.2 carry-forward.
- Integration: **20 passed** (real containers) incl. 1 new — full live round-trip: upload a doc containing a fact that exists nowhere else (`QX-4471-ZY`), ingest it for real, POST `/v1/rag/query` with a question about that fact, assert `degraded=False`, the fact string appears in the generated answer, and every citation carries a resolvable `chunk_ref`/`document_id`.
- **AC 3.3:** proven exactly as worded — "question over seeded docs returns grounded answer object with citations" — via the live integration test above, at the API level, no chat UI involved.
- Full gate: `ruff check .` clean, `mypy apps` → same 12 pre-existing Sprint-1 errors (0 new), `pytest tests/unit` 126/126, `pytest tests/integration` 20/20.

Issues (symptom → root cause → resolution; solved logged too):
- Initial `Hit`/`Citation` design used an integer `chunk_id` mirroring the `chunks` table's PK, but that PK is assigned by Postgres *after* the Qdrant upsert in the current ingestion ordering (worker.py inserts chunk rows once the pipeline returns), so it was never available to put in the Qdrant payload at write time. Caught before wiring the live endpoint: switched `Hit`/`Citation` to a `chunk_ref: str` carrying `content_sha256` (already known and unique per chunk) instead of introducing a two-phase insert-then-upsert just to get the PK first. RESOLVED — no reordering of the 3.1 pipeline needed.
- LLM citation markers as raw chunk hashes (`[chunk:9f8a...]`) would be unwieldy in the prompt/response — switched to 1-indexed *positions* into the retrieved-hits list (`[chunk:1]`, `[chunk:2]`, ...), resolved back to the real `Hit`/`chunk_ref` server-side in `_resolve_citations`. RESOLVED (design decision made during TDD, not a bug).

Notes / deviations:
- "Hybrid retrieval (dense + keyword filter)" is implemented as dense kNN narrowed by a Qdrant full-text `MatchText` filter on chunk content, not sparse-vector (BM25/SPLADE) fusion — matches the literal task wording; true sparse+dense fusion would need a second named vector configured at ingest time and is a larger change than this task's scope. `/v1/rag/query`'s `keyword` field is optional and currently unused by any caller (Sprint 4's chat UI is the natural first consumer of the keyword parameter, if a caller-supplied keyword hint proves useful in practice).
- The generation call always uses `reasoning()` (not `utility()`) since answer synthesis is a judgment/generation call-site per TRD §4.3, and per CLAUDE.md rule 10 this is a deliberate choice: RAG answers need the stronger model's grounding/citation discipline, not the cheaper tier.
- No per-agent config table lookup yet — `AgentQueryConfig` is currently passed with defaults from the `/v1/rag/query` request (`top_k` only); wiring real per-agent `max_context_tokens`/caps from the `agents` table (§11) lands with the agent runtime in Sprint 4.

## 2026-07-21 — 3.4 web shell + Knowledge UI — DONE

Built (Sprint 3, branch `feat/sprint-3-rag`):
- **Web shell (`apps/web`):** upgraded `next` 15.1.0→15.5.20 (fixes CVE-2025-66478, flagged by pnpm on install — patched rather than left in place). Added Tailwind v4 (CSS-first, `postcss.config.mjs` + `app/globals.css` with light/dark CSS variables), `next-auth` v5 beta + Keycloak provider (`lib/auth.ts`) wired to the `fleet-api` confidential client already seeded in `infra/compose/keycloak/fleet-realm.json`, `next-intl` (TR/EN, cookie-based locale — `i18n/request.ts`/`i18n/locales.ts`, `messages/{en,tr}.json`), root layout with session + i18n providers and a `NavBar` (sign-in/out, locale switcher), an `(app)` route group that gates its children behind a real session.
- **`packages/shared` gained a real typed client**, not just types (CLAUDE.md: "API access only through packages/shared client"): `src/client.ts` wraps `openapi-fetch` over the generated `paths`, injecting the session's bearer token via middleware. Regenerated `openapi.json`/`schema.d.ts` to include all Sprint 2/3 endpoints (previously only had the Sprint-1 skeleton routes).
- **Knowledge screens** (`app/(app)/knowledge`, `components/knowledge/`): `KnowledgeBrowser` (collection list → document list, both via the real `/v1/collections`/`/v1/documents`), `UploadForm` (multipart upload through the typed client), `DocumentStatusBadge` (pending/queued/ready/error, localized). Live status: the browser polls `/v1/documents?collection_id=` every 2s **only** while any listed document is `pending`/`queued`, stopping once nothing is in flight (AC 3.4).
- **Small shadcn-style UI kit** (`components/ui/`): Button, Card, Badge — Tailwind + `class-variance-authority` + Radix `Slot`, matching TRD §3's stack choice without pulling in the full shadcn CLI scaffold.
- **`fleet_api` CORS middleware** (`app.py`, new `Settings.web_origin`): the browser-side Knowledge UI calls `/v1/*` cross-origin (`:3000` → `:8000`) — this didn't exist before this task.
- **NextAuth access-token refresh** (`lib/auth.ts`'s `jwt` callback): Keycloak access tokens are short-lived (~5 min default) but a Knowledge session (upload + live-poll) easily outlasts that; the JWT callback now tracks `accessTokenExpires` and calls Keycloak's `refresh_token` grant before it lapses, surfacing `session.error` if the refresh itself fails so the browser can stop polling instead of looping on 401s.
- **`Makefile` gained `api`/`web` targets** (`uvicorn --reload` / `pnpm --filter web dev`) — referenced in CLAUDE.md's Commands section since Sprint 1 but never implemented until this task.

Verified (typecheck/lint/build + manual end-to-end against the live stack — no headless-browser tool is available in this environment, so verification is HTTP-level: real Keycloak OIDC login via curl following every redirect/cookie/CSRF step exactly as a browser would, not a mocked session):
- `apps/web`: `tsc --noEmit` clean, `eslint .` clean (excluding the gitignored, auto-generated `next-env.d.ts`), `next build` succeeds (production bundle, SSG passes) on both the initial pass and after the auth-refresh addition. A first build caught a real bug: `locale-switcher.tsx` (client component) importing from `i18n/request.ts` (server-only, imports `next/headers`) — fixed by splitting locale constants into `i18n/locales.ts`.
- `packages/shared`: `tsc --noEmit` clean after adding the runtime client.
- **Live end-to-end (HTTP-level, real services):** completed the full Keycloak authorization-code+PKCE flow as `builder` (CSRF token → signin POST → Keycloak login form → authorization code → NextAuth callback → real `authjs.session-token` cookie); loaded `/knowledge` server-side with that session and confirmed it rendered a seeded collection via a real `/v1/collections` call; uploaded a document through the exact multipart path the `UploadForm` component uses, got `201`/`status:"queued"`; ran the real `arq` worker (`--burst`) to process it; re-fetched `/v1/documents/{id}` and confirmed `status:"ready"` — the live status transition the polling loop is built to surface (AC 3.4, "Knowledge UI shows ingestion states live").
- **CORS bug found and fixed live:** the first CORS wiring attempt returned 405 on the browser's preflight OPTIONS request — root-caused to Starlette middleware ordering (wraps in *reverse* add-order; CORSMiddleware must be added *last* to be outermost) rather than first as originally written. Re-verified 200 + correct `access-control-allow-origin` after the fix, then locked it in with two new integration tests (`test_cors_preflight_allows_configured_web_origin`, `test_cors_rejects_unconfigured_origin`).
- Token-refresh mechanism verified by directly exercising Keycloak's `refresh_token` grant with the same `fleet-api` client credentials `lib/auth.ts` uses — confirmed it returns a genuinely new access token, not a live 5-minute wall-clock wait (which was inconclusive: Keycloak's SSO cookie made a fresh re-login indistinguishable from a token-refresh from the outside without decoding session internals more deeply than useful).
- Full gate: unit `pytest tests/unit` 126/126 (unchanged from 3.3 — no new Python unit surface in 3.4 beyond CORS, covered by integration), integration `pytest tests/integration` 22/22 (2 new CORS tests), `ruff check .` clean, `mypy apps` → same 12 pre-existing errors (0 new).

Issues (symptom → root cause → resolution; solved logged too):
- `pnpm add next` flagged `next@15.1.0`'s CVE-2025-66478 on install → upgraded to the latest 15.x patch (`15.5.20`, staying off the major-version-16 jump mid-sprint) → vulnerability warning gone on reinstall. RESOLVED.
- Browser-side calls to `/v1/*` failed cross-origin (no CORS middleware existed on the API at all before this task) → added `CORSMiddleware` gated behind `with_middleware` like the other cross-cutting middleware, restricted to `settings.web_origin` (not `*`, since credentials are involved). First attempt still 405'd preflights → Starlette middleware wraps in reverse add-order, so CORS (which must run first/outermost to short-circuit OPTIONS) was actually innermost → moved the `add_middleware(CORSMiddleware, ...)` call to last. RESOLVED, regression-locked with 2 new integration tests.
- The multipart file-upload endpoint (`POST /v1/documents`) needed `python-multipart`, not installed by default with FastAPI → added as an explicit `fleet-api` dependency (caught immediately by the app failing to import the router at all, before any manual testing). RESOLVED.
- Collections API's `POST`/`PATCH`/`DELETE` require `MANAGE_DEPT`, which — per the gap already logged in the 3.2 entry — no seeded Keycloak user holds by exact role-string match. Worked around identically to 3.2/3.3: seeded/cleaned demo collections directly via SQL for browser testing, exercised only the `GET` (UPLOAD-gated) live through the real UI/API. Same pre-existing gap, not newly introduced or fixed here.

Notes / deviations:
- No `next-intl` locale-in-URL routing (`/en/knowledge`, `/tr/knowledge`) — used a cookie-based single-tree approach instead, which is faster to wire for a two-locale demo-scale app and matches how the locale switcher needs to behave (persist across navigation without changing the URL structure other screens will link to). Revisit if SEO/shareable-locale-URLs become a requirement.
- The Chat screen, My Approvals, and Workflow catalog (also listed under "End-user" in TRD §12) are explicitly out of scope for 3.4 — task 3.4's text names only "Knowledge screens (upload, status, browse)"; Chat lands in Sprint 4 task 4.3.
- No headless-browser/screenshot tool was available in this environment to visually confirm the rendered UI pixel-for-pixel; verification instead exercised the actual HTTP contract every browser action produces (real OIDC redirects/cookies, real multipart upload, real polling target) end-to-end against the live stack. If a visual regression exists in layout/styling that doesn't affect the HTTP contract, it would not have been caught by this verification pass.
- shadcn/ui's own CLI scaffold was not run; a small hand-written set of the 3 primitives actually needed (Button/Card/Badge) was added instead, following the same class-variance-authority + Radix + Tailwind conventions shadcn generates, to avoid pulling in components unused by this task's screens.

## 2026-07-21 — 4.1 runtime core (LangGraph base graph + Postgres checkpointer) — DONE

Built (Sprint 4, branch `feat/sprint-4-runtime-chat-agent`):
- **`agents`/`prompt_versions`/`conversations`/`messages`/`feedback`/`approvals` tables** (migration `0005_agents_chat_approvals`, ORM classes in `apps/api/fleet_api/models.py`, TRD §11 schema) — the runtime's persistence surface; `approvals` is needed now even though its UI is Sprint 5 task 5.4, since the HITL interrupt/resume AC requires somewhere to eventually record the decision.
- **`fleet-runtime` gained `langgraph`, `langgraph-checkpoint-postgres`, `psycopg[binary]`, `redis`** — `psycopg[binary]` specifically (not plain `psycopg`, which needs a system `libpq` this Windows box doesn't have).
- **`core/guardrails.py`** (promoted out of `fleet_rag`, CLAUDE.md rule 4): `wrap_untrusted()` — the single place untrusted content gets quarantined before reaching a prompt — plus `detect_injection()` (TRD §7.3 instruction-like-pattern/encoded-payload heuristic). `fleet_rag/query/service.py` now imports this instead of keeping a private copy (no behavior change — same `<untrusted_context>`/`[chunk:N]` wire format, proven by the unchanged 3.3 unit tests staying green).
- **`core/memory.py`**: `build_context()` — rolling conversation window (verbatim up to `max_turns`) + LLM-summarized eviction of older turns via the utility model (§5 context budgeting, §4.3 summarization is a utility call-site).
- **`core/citations.py`**: generic `Citation` dataclass + `attach_citations()` — the carrier the graph's citation-attach node uses regardless of which tool/agent produced the citations; RAG-specific grounding (structural check) stays in `fleet_rag.query.answer`, not duplicated here.
- **`core/hitl.py`**: `requires_approval()` — pure TRD §9 risk_class decision (`read` always autonomous; `write:external` always the approval queue, no exception; `write:internal` autonomous only once both eval pass-rate ≥ 0.9 and dept_admin-enabled autonomy hold).
- **`core/graph.py`**: `build_graph(AgentSpec, llm_client, checkpointer)` — the shared LangGraph base graph every agent compiles against: `context_builder` → `guardrails_in` (injection heuristic on the latest user turn) → `call_model` (routes to `llm_client.reasoning()` or `.utility()` per `AgentSpec.call_tier`) → conditional edge to `hitl` (calls LangGraph's `interrupt()` with `{tool, args, risk_class}` when `core.hitl.requires_approval` says so) or straight to `execute_tool` → `citation_attach`. Resume is a `Command(resume={"approved": bool})` back into the same `thread_id`; rejection short-circuits to `citation_attach` without calling the tool.

Verified (unit + live against the compose stack):
- Unit: **149 passed** (18 new: 7 guardrails, 3 memory, 3 citations, 5 hitl carried into the graph tests below, 5 graph) — incl. the exact AC wording: routing utility-vs-reasoning (2 tests, asserting the *other* tier's call list stays empty), interrupt fires on a `write:external` tool call (asserts `__interrupt__` present with `{tool, risk_class}` payload), resume completes (asserts the tool actually ran and `tool_result` is set), plus a resume-after-rejection case (tool never called, `rejected=True`) that goes beyond the literal AC text but is the other half of the same HITL contract.
- Integration: **23 passed** (1 new) — `test_runtime_graph_live.py` builds the SAME graph against a **real `AsyncPostgresSaver`** (not `InMemorySaver`): interrupts, then discards the graph object and rebuilds a fresh one bound to the same Postgres-backed thread_id before resuming — proving resume works off *persisted* checkpoint state, not in-process Python memory (the scenario that actually matters for a runtime pod restart).
- Full gate: `ruff check .` clean, `mypy apps/runtime` clean (15 files), `pytest tests/unit` 149/149, `pytest tests/integration` 23/23 (no cross-test event-loop-policy leakage from the new Windows fixup below).

Issues (symptom → root cause → resolution; solved logged too):
- `psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode` on the live checkpointer test → psycopg's async mode is incompatible with Windows' default Proactor loop (a psycopg/Windows limitation, not a Fleet bug — production runs under uvicorn on Linux and is unaffected) → set `asyncio.WindowsSelectorEventLoopPolicy()` at module load in `test_runtime_graph_live.py` only (same class of Windows-only test-infra fixup as the asyncpg event-loop notes in the Sprint 3 live tests). Verified it doesn't leak into other integration tests by running the full `tests/integration` directory together (23/23 pass, no new failures). RESOLVED.
- No other issues — the graph design (conditional-edge routing to `hitl` vs `execute_tool` vs straight-through `citation_attach`) worked on the first real implementation attempt against all 5 unit tests including interrupt/resume.

Notes / deviations:
- The **Support Copilot agent itself** (the concrete `AgentSpec` + `agents/support_copilot/{prompt.md,graph.py,tools.py,eval/}` per CLAUDE.md's repo layout) is task 4.4, not 4.1 — 4.1 delivers only the shared base graph + core nodes every agent will compile against. No agent-specific prompt/tools exist yet.
- `core.graph`'s `call_model` node expects a `tool_call` attribute on the LLM response (`{"name": ..., "args": {...}}`) to decide whether to route to HITL — this is a convention the per-agent graph's model-calling wrapper must produce (e.g. by parsing structured output), not something `LLMClient.reasoning()`/`.utility()` return natively today (they return free-text `content`). Task 4.4's Support Copilot (pure RAG, no tools per its Wave 0 spec) doesn't need this path at all; the first agent that actually exercises live tool-calling is Sprint 5 (Analytics/Jira/GitHub/Slack agents), which is where this convention gets its first real caller and may need revisiting.
- `core.memory.build_context`'s summary is produced but the base graph (`core.graph`) doesn't yet call it — wiring a real conversation's rolling history through `build_context` before `call_model` is per-agent (each agent's own `context_builder` override), matching the module docstring's "per-agent memory/KB augmentation happens here in a real agent's own node."

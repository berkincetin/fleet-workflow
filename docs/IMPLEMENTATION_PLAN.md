# Fleet — Implementation Plan (Sprint Backlog)

**Goal:** A demoable, Kubernetes-ready platform: core (gateway, RBAC, budgets, observability, RAG, runtime, MCP, approvals, admin) + 3 department agents + 2 n8n automations + local-model KVKK lane + tests/evals/load-smoke in CI.

**Method:** AI-first development with Claude Code. Work is organized as **ordered sprints of numbered tasks** (e.g. `3.2`). There is no calendar deadline; the sprint order **is** the priority order. Tasks are executed strictly in sequence unless marked **[DEFERRABLE]**. Every completed task leaves the repo in a runnable state (`make dev` green, tests green).

**How work is assigned:** the user requests tasks by number — e.g. *"1.1-1.3 görevlerini yap"* means implement tasks 1.1, 1.2, 1.3. Execution follows the **Task Execution Protocol in CLAUDE.md**: implement → write & run tests → verify each task's AC → report findings → on any failure, diagnose and report the root cause and **wait** for the user's decision before attempting fixes.

Legend: **AC** = acceptance criteria (must be verified true when the task is reported done). **[DEFERRABLE]** = may be postponed without blocking later tasks.

---

## Sprint 0 — Prerequisites (user-assisted)

These items require the user (API keys, hardware, external accounts). They do **not** all need to be ready up front: Claude Code requests each one **at the moment the depending task needs it** (per the Task Execution Protocol) and pauses until provided.

- **0.1** API keys in `.env` (never committed): **Anthropic + OpenAI + Gemini**; pin exact model IDs in `gateway/litellm/config.yaml` per TRD §4.2. *(first needed: 2.1)*
- **0.2** Ollama installed **host-native with NVIDIA GPU**: `nvidia-smi` OK → `ollama pull qwen2.5:7b-instruct-q4_K_M` (pull 14b variant if VRAM ≥12 GB) → `ollama pull bge-m3` (local embeddings for pii lane). *(first needed: 2.3 live test; hard requirement in Sprint 8)*
- **0.3** Sandbox GitHub repo + PAT with repo scope (target of the **Dev Agent**, distinct from this project's own repo created in 1.0); Slack incoming webhook. *(first needed: 5.3)*
  *(The SMTP sandbox — mailpit — is a compose service added in 1.1, not a user-provided prerequisite; the email MCP server first needs it in 5.1.)*
- **0.4** Containers reach host Ollama via host gateway (compose `extra_hosts: host.docker.internal:host-gateway`; k3d equivalent in values-dev). *(verified with a LiteLLM test call in 2.3)*

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

## Sprint 2 — LLM Gateway, Model Registry, Budgets

- **2.1 LiteLLM proxy.** Config template + pricing sync script.
  **AC:** proxy boots from generated config; pricing sync produces valid model prices.
- **2.2 Model registry.** `models` table + admin CRUD API + smoke-test-on-add.
  **AC:** adding a model via API triggers connectivity/capability smoke test; result stored.
- **2.3 Gateway client (`core/llm`).** Tiering helpers, sensitivity routing enforcement — including the **redaction-downgrade rule (TRD §8)** — retries/fallbacks, Langfuse callback, token/cost capture → `spend_ledger`.
  **AC:** unit: sensitivity refusal, fallback chain; live call through LiteLLM to one cloud model **and** one Ollama model recorded in Langfuse + spend_ledger.
- **2.4 Budgets.** Budgets table + pre-check middleware + 80%/100% behavior.
  **AC:** unit: budget hard-stop; soft-limit flag surfaced in response metadata.

## Sprint 3 — RAG

- **3.1 Ingestion pipeline.** MinIO upload API; arq worker: extract (pdf/docx/txt/img) → OCR (vision-LLM primary, tesseract fallback) → Presidio PII scan (TR recognizers) with per-collection policy → structure-aware chunking → dedup by sha → embed (utility model) → Qdrant upsert with metadata.
  **AC:** upload sample PDF + scanned image → chunks searchable; re-upload of the same doc costs 0 new embeddings.
- **3.2 Collections + retention.** Collections API with sensitivity + retention + pii_policy; retention purge job.
  **AC:** PII doc in `pii` collection gets redacted variant; purge removes expired chunks/files/vectors.
- **3.3 Query + citations.** Hybrid retrieval (dense + keyword filter), per-agent top_k/token caps, citation payloads; chat-less test harness endpoint `/v1/rag/query`.
  **AC:** e2e (API-level): question over seeded docs returns grounded answer object with citations.
- **3.4 Web shell + Knowledge UI.** Next.js shell (auth, layout, i18n) + Knowledge screens (upload, status, browse).
  **AC:** Knowledge UI shows ingestion states live.

## Sprint 4 — Agent Runtime, Chat, First Agent

- **4.1 Runtime core.** LangGraph base graph + Postgres checkpointer; core nodes: context builder (KB + memory w/ rolling summary), guardrails (wrap_untrusted, injection heuristics, output schema check, **structural grounding check per TRD §9**), HITL interrupt node, citation attach.
  **AC:** unit with FakeLLM: routing utility-vs-reasoning, interrupt fires on write:external tool, resume completes. *(The approval UI ships in 5.4; until then interrupt/resume is exercised at the API/fixture level — no agent has a `write:external` tool before Sprint 5, so the missing UI blocks nothing.)*
- **4.2 Agent registry + semantic cache + kill switches.** Agent registry/config API; semantic cache (opt-in) in Redis, threshold per TRD §5; **kill switches per TRD §9 — per-agent `status=paused` (instant, cached 5s) enforced in the runtime before any node runs, and a global read-only mode flag.** The Admin UI buttons for these land in 7.1; the enforcement mechanism is built here.
  **AC:** cached answer path returns with badge flag; cache invalidates on KB collection update; a paused agent stops accepting runs within 5s (unit + integration); global read-only mode blocks all `write:*` tool execution.
- **4.3 Chat UI.** SSE chat with streaming, citations, feedback buttons.
  **AC:** streamed answer renders with citations; 👍/👎 lands in Langfuse.
- **4.4 Support Copilot (agent #1, cloud lane).** Configured over seeded help-center docs; eval dataset (15 cases) + runner + CI gate wiring; Playwright E2E suite bootstrapped (login → chat → cited answer) and wired to nightly CI per TRD §13.3 — later flows (upload, approvals, admin) extend this suite in their own tasks.
  **AC:** demo path: login → chat → grounded cited answer; `make eval AGENT=support_copilot` ≥ threshold; `make e2e` green on the demo path.
- **4.5 [DEFERRABLE] Agent Builder v1.** Prompt editor + versions, model pickers, KB selection, tool allowlist, sensitivity, sandbox chat. Until built, agents are configured via seed/config API — this does not block any later task.
  **AC:** create + edit an agent end-to-end from the UI; prompt version diff visible.

## Sprint 5 — MCP, Agents #2–3, Approvals

- **5.1 MCP base + first servers.** MCP base package (risk_class, schemas, auth); servers: pg_ro (allowlist + auto-LIMIT + timeout), ocr, email (SMTP sandbox), internal-mock.
  **AC:** each server passes contract tests; risk_class declared per tool.
- **5.2 Analytics agent (agent #2).** Text-to-SQL over governed views (fixtures from 1.2), SQL shown, read-only role; evals (result-set match).
  **AC:** integration: business question → table + SQL; query attempt on non-allowlisted table is refused and logged.
- **5.3 Jira/GitHub/Slack MCP.** Jira (fixture-backed mock + real-config option), GitHub (sandbox repo), Slack (webhook).
  **AC:** contract tests green against mocks; GitHub sandbox smoke (branch create) works with PAT.
- **5.4 Approval queue.** Approval queue UI (context, diff, approve/edit/reject) + interrupt/resume wiring.
  **AC:** a pending write:external item can be approved (run resumes) or rejected (run cancels cleanly).
- **5.5 Dev Agent (agent #3).** Graph: ticket → plan → branch `agent/*` → PR draft → Slack notify; PR creation classified write:external ⇒ approval. Eval dataset (≥15 cases per DEPARTMENT_SCENARIOS §Dev Agent) + runner + CI gate wiring, same pattern as 4.4.
  **AC:** e2e: labeled mock ticket → pending approval → approve → PR exists on sandbox repo → Slack message; reject path cleanly cancels; all steps in one Langfuse trace; `make eval AGENT=dev_agent` ≥ threshold. *(Fallback: may run in fixture mode if live GitHub sandbox is unavailable.)*

## Sprint 6 — n8n Automations

- **6.1 n8n queue mode.** Main + worker in compose/Helm; SSO-proxied subdomain; Fleet API key issuance/validation service (hashed, scoped, expiring per TRD §7.1) + service keys for n8n.
  **AC:** n8n reachable behind SSO proxy; a trivial workflow executes on a worker and calls the Fleet API with an issued key; a revoked key gets 401.
- **6.2 Automation #1 — weekly summary.** Cron → pg_ro via Fleet API → Slack.
  **AC:** runs end-to-end in dev.
- **6.3 Automation #2 — invoice intake.** Webhook/manual upload → OCR extract → draft entry → approval queue. Workflow JSONs exported to repo. Eval dataset (≥12 cases per DEPARTMENT_SCENARIOS §Invoice — extraction-type threshold, see §13.4) + runner wiring. *(UI polish is deferrable; the API path + approval flow is the required part.)*
  **AC:** invoice draft appears in approval queue with extracted fields; both workflows re-import cleanly on a fresh stack; `make eval AGENT=invoice_intake` ≥ threshold.

## Sprint 6.5 — Platform UI & Scenario Showcase

Everything built in Sprints 1–6 is API-only or fixture-only for most of what a non-technical user would touch (dev/invoice agent runs, n8n workflows, eval examples, admin CRUD). This sprint integrates all of it into a Turkish-first, plain-language web UI — no new agent capability is built here. It also turns the six not-yet-built department scenarios (HR completion, Listing Quality, Vehicle Intake, Insights Publisher, Dealer Onboarding, Legal Review) into "coming soon" cards backed by real sprint tasks (8.5, Sprint 11, Sprint 12 below), so the showcase is honest about what's live vs planned.

- **6.5.1 Docs restructuring.** Insert this sprint + Sprint 11/12 + task 8.5 into the plan; update TRD §12 (Workflow catalog P2→CORE; add Examples gallery + Home/Department hub); update `docs/split/INDEX.md` and the wave-plan table with target sprint numbers. Original + split parts edited together.
  **AC:** `docs/split/` mirrors this section; TRD §12 no longer lists Workflow catalog as [P2]; wave-plan table's "ships when" column is filled for all 10 scenarios.
- **6.5.2 Examples backend.** New `eval_cases` DB table seeded from `evals/datasets/*.jsonl` (source=seed); `GET/POST /v1/examples` (agent-scoped, schema-validated per agent); `evals/promote.py` to export UI-created (source=user) cases back to jsonl for a builder to version. `evals/runner.py` and CI eval gate stay jsonl-driven and untouched.
  **AC:** seeding is idempotent and matches jsonl line counts per agent; a case created via API appears in `GET /v1/examples`; `make eval AGENT=x` still passes unchanged.
- **6.5.3 n8n client + workflows router.** `n8n_client.py` (httpx, never raises — connect failure surfaces as `reachable:false`); `GET /v1/workflows` (catalog + live n8n state), `POST /v1/workflows/invoice-intake/run` (image upload → n8n webhook proxy), `POST /v1/workflows/weekly-summary/run`, `POST /v1/workflows/{slug}/activate|deactivate`. Small additions: `GET /v1/dev-agent/tickets` (fixture tickets for a picker UI), `GET /v1/agents/global/read-only` (state for the kill-switch toggle). `make client` regenerates the TS client.
  **AC:** catalog reflects real n8n state; n8n stopped → API still returns 200 with `reachable:false`; RBAC gates verified (member cannot activate/deactivate).
- **6.5.4 Compose + workflow import.** n8n loopback port (127.0.0.1:5678) for the Fleet API to reach the REST API directly (oauth2-proxy remains the only human entry at :5679); `workflows/weekly-summary.json` gets a second manual-run webhook trigger; `make n8n-import` target (import + activate both workflows on a fresh stack); `.env`/README document `N8N_API_KEY` (created once in the n8n UI — no headless bootstrap exists).
  **AC:** fresh `make dev && make n8n-import` leaves both workflows active and callable from the Fleet API.
- **6.5.5 Session roles + app shell + UI primitives + i18n scaffolding.** Decode Keycloak `realm_access.roles` into the next-auth session (nav gating only — server keeps enforcing RBAC); new sidebar app shell (Ana Sayfa, Sohbet, Senaryolar, Otomasyonlar, Örnekler, Bilgi Bankası, Onaylar, Yönetim); new shadcn-style primitives (dialog, select, tabs, table, textarea, input, toast) on the existing CVA/CSS-var conventions; new i18n namespaces in `tr.json`/`en.json` (Turkish written first, no technical jargon in user-facing copy).
  **AC:** nav items show/hide per role; TR/EN switch covers all new copy; `tsc`/lint green.
- **6.5.6 Home dashboard + Department hub.** Redesigned home with big task cards (role-aware); `/scenarios` page with all 10 department scenarios — 4 live + HR partial + 5 "coming soon" with their target sprint badge — deep-linking into chat/automations/examples.
  **AC:** coming-soon cards show the correct target sprint (8.5 / 11.x / 12.x) and are non-clickable; live cards deep-link correctly.
- **6.5.7 Automations catalog UI.** `/automations` page: friendly workflow cards, invoice image upload → run → link to the resulting approval, weekly-summary manual run, activate/deactivate toggle (role-gated), plain-language "n8n is down" banner, advanced link to the n8n editor for admins only.
  **AC:** uploading a sample invoice image from the UI produces a pending approval; approving it resumes the run; stopping n8n shows the down-banner within one refresh.
- **6.5.8 Examples gallery + clickable HITL demo.** `/examples` page: per-agent tabs, "try it" (chat prefill for support_copilot/analytics; ticket-picker run dialog for dev_agent; image-upload run for invoice_agent), create-new-example form → `POST /v1/examples`. Chat page accepts `agent`+`prefill` query params.
  **AC:** every one of the 4 live agents has a working try-it path entirely from the UI; a newly created example appears in the gallery immediately.
- **6.5.9 Admin section (existing APIs only).** `/admin` with agents (CRUD, pause/resume, global read-only toggle), models (registry + smoke test), API keys (issue with scope picker, one-time reveal, revoke) — budgets/users-roles/cost-dashboard stay out (their APIs don't exist until Sprint 7).
  **AC:** pausing an agent from the UI blocks its runs within 5s; adding a model runs the smoke test from the UI; a revoked key is rejected on its next request.
- **6.5.10 E2E + polish pass.** Playwright flows for the new surfaces (role-based home, automation states, examples try-it); TR copy review pass; full `make dev` fresh-stack walkthrough of the showcase.
  **AC:** nightly e2e green; a non-technical user can complete the full showcase (chat, an automation run, an example try-it, an admin action per their role) without touching the terminal.

## Sprint 7 — Admin & Observability

- **7.1 Admin: users/roles, budgets editor.** Users/roles screens; budgets editor. *(Models CRUD+smoke, and API key management shipped early in 6.5.9 — this task only adds what 6.5 didn't cover.)*
  **AC:** role change takes effect on next request.
- **7.2 Cost dashboard, approvals, audit explorer.** Spend by dept/agent/model, burn-down, cache savings; approvals all-dept view; audit explorer (filter + Langfuse deep-link).
  **AC:** audit row deep-links to its trace; dashboard renders with seeded traffic.
- **7.3 [DEFERRABLE] Admin system-health screen.** Queues/workers/providers. Grafana suffices in the meantime.
  **AC:** health screen reflects a stopped worker within one refresh.
- **7.4 Grafana + alerting as code.** Dashboards provisioned as code; Alertmanager → Slack rules (budget, error rate, latency, queue depth, cost anomaly: dept daily spend > 3× 7-day average per TRD §5).
  **AC:** budget soft-limit triggers Slack+UI warning in a scripted test.

## Sprint 8 — KVKK Lane

- **8.1 Local-lane quality rehearsal.** Run Tesseract `tur` + local Qwen on realistic **synthetic** TR CV and invoice scans; measure extraction accuracy against the eval thresholds; select demo fixtures based on results; if below threshold, report findings and options (14b model, image preprocessing, [P2] local VLM) — decision stays with the user.
  **AC:** findings report with accuracy numbers per document type; demo fixture set chosen.
- **8.2 HR CV mini-flow (pii lane).** HR `pii` collection + CV parse task pinned to Ollama; bge-m3 embeddings. **CI note:** the "no cloud egress" assertion is split — a GPU-free unit/integration test asserts routing *targets* (which model the gateway resolves to) on GitHub-hosted runners, while the full local-model extraction eval that needs Ollama+GPU runs on a self-hosted GPU runner (or nightly, marked `@pytest.mark.gpu` and skipped on hosted runners). Local-lane evals never gate hosted-runner PR CI.
  **AC:** integration test proves a `pii` request never reaches a cloud provider (recorded gateway targets) — runs on hosted CI without GPU; CV → structured profile via local model verified on the GPU lane.
- **8.3 Erasure + clearance surfacing.** Erasure endpoint; retention job verified; sensitivity clearance matrix surfaced in Admin→Models.
  **AC:** erasure removes subject data, audit preserved pseudonymized.
- **8.4 PII masking verification.** Masking verified in logs/traces.
  **AC:** detected identifiers appear masked in Loki and Langfuse for a seeded PII conversation.
- **8.5 HR Talent & Onboarding scenario completion.** Wrap the 8.2 CV mini-flow into a full `hr_agent` per DEPARTMENT_SCENARIOS §5: role-match shortlist draft (write:internal, dept_admin approval), `hr-policies` cloud-lane Q&A alongside the `hr-cvs` pii-lane CV parse; eval dataset (≥15 cases per spec — extraction accuracy, protected-attribute schema-exclusion, onboarding Q&A grounding); flip the HR scenario card from "partial" to live in `/scenarios`.
  **AC:** `make eval AGENT=hr_agent` ≥ threshold; a synthetic CV produces a structured profile with protected attributes excluded; HR scenario card is live end-to-end from the UI.

## Sprint 9 — Hardening

- **9.1 Load.** k6: chat_smoke + mixed_day against k3d; fix hotspots (pool sizes, HPA values).
  **AC:** SLO thresholds pass in k6 report (stored in repo).
- **9.2 Security.** `make scan` clean of high-sev; in-repo injection corpus vs Support Copilot, findings triaged.
  **AC:** injection corpus: 0 successful instruction-follows from quarantined content.
- **9.3 [DEFERRABLE] Chaos-lite + garak.** garak probe suite; kill-switch drill (pause agent mid-load); pod-kill during agent run → resume from checkpoint verified. *(Injection corpus tests in 9.2 are NOT deferrable.)*
  **AC:** resume test green; kill switch takes effect ≤5s under load.
- **9.4 Backup & restore drill.** CloudNativePG scheduled backups (WAL → MinIO), Qdrant nightly snapshots → MinIO, MinIO versioning enabled (TRD §14); restore runbook exercised.
  **AC:** Postgres point-in-time restore and a Qdrant snapshot restore succeed on a scratch k3d cluster; `docs/runbooks/restore.md` updated with the actual commands used.

## Sprint 10 — Demo Assembly & Docs

- **10.1 Fresh-install rehearsal.** Finalize README (install steps, demo walkthrough — bootstrapped in 1.1); `make k3d-up` from README alone on a clean machine; demo seed scenario data.
  **AC:** clean machine → running demo in ≤30 min following README.
- **10.2 Docs + release.** Runbooks (restore, on-call basics); demo script (below) dry-run; screenshots/GIFs for the deck; tag v0.1.0. A tag-triggered GitHub Actions release pipeline (TRD §14) runs the full check suite and builds the release images.
  **AC:** the tag pipeline runs all CI jobs green on the `v0.1.0` tag; dry-run completes within 15 min.

## Sprint 11 — Wave 1 Scenarios

Post-MVP onboarding of the three Wave 1 department scenarios (docs/split/department-scenarios/06-08), following the generic checklist in `department-scenarios/99-onboarding-checklist.md`. Each flips its `/scenarios` card from "coming soon" to live on completion.

- **11.1 Listing Quality (Listings Ops).** `listing_quality` agent — vision Gemini Flash, reasoning Claude Sonnet (escalations only), utility Gemini Flash, sensitivity internal, semantic_cache off. Tools: `listings.get_new`/`listings.flag` (INTEGRATION-POINT mock listing API + synthetic listing generator), `pg_ro.query` price-index view. n8n workflow: new-listing webhook → agent → flag/pass, plus nightly batch re-check job. Flag-only guardrail (agent never unpublishes). Eval dataset ≥20 (photo/description mismatch, blurred-plate detection, clean-listing false-positive control ≥85% precision).
  **AC:** shadow mode 2 weeks (flags logged, not shown) verified in a scripted run; `make eval AGENT=listing_quality` ≥ threshold; scenario card live.
- **11.2 Vehicle Intake (Trink sat!).** `vehicle_intake` agent — vision Gemini Flash (photos non-PII after plate-mask step), local OCR for expertise PDFs (owner PII) → redact → cloud reasoning on redacted brief, sensitivity confidential, no write tools. Tools: `ocr.extract` (local), `pg_ro.query` comparables/price-index views. Eval dataset ≥15 (chassis/km/damage-table extraction, price-band sanity vs fixture comparables, missing-report → "incomplete" with no invented values).
  **AC:** `make eval AGENT=vehicle_intake` ≥ threshold; missing-report fixture never invents values; scenario card live.
- **11.3 Insights Publisher (Marketing).** `insights_publisher` agent — reasoning Claude Sonnet, utility Gemini Flash, sensitivity internal, semantic_cache off. Knowledge: `mkt-brand` (brand-voice guide, past reports). Tools: `pg_ro.query` index views (read), `cms.publish`+`social.post` (**write:external → approval**, INTEGRATION-POINT mock CMS/social). n8n workflow: cron monthly 1st 08:00 → data pull → draft → approval → publish; failure → Slack alert. Guardrail: every numeric claim must match an attached query result. Eval dataset ≥10 (numbers-match assertion, brand-voice rubric judge ≥4/5, no-invented-statistics test).
  **AC:** monthly cron produces a draft with grounded numbers pending approval; `make eval AGENT=insights_publisher` ≥ threshold; scenario card live.

## Sprint 12 — Wave 2 Scenarios

Post-MVP onboarding of the two Wave 2 department scenarios (docs/split/department-scenarios/09-10), both requiring the local KVKK lane from Sprint 8.

- **12.1 Dealer Onboarding (Corporate Sales).** `dealer_onboarding` agent — pii lane for documents (local OCR + local extraction for tax no/IBAN), cloud utility allowed for non-PII orchestration text, sensitivity pii. Tools: `ocr.extract` (local), `crm.get_application` (read, INTEGRATION-POINT), `email.send` (**write:external → approval** initially, supervised auto-send for the missing-doc template after eval history), `crm.update_status` (write:internal). Eval dataset ≥12 (certificate field extraction, name-mismatch fixture → flag, TR formal-tone email template correctness).
  **AC:** approval-gated outbound email verified for the first month's rollout mode; `make eval AGENT=dealer_onboarding` ≥ threshold; scenario card live.
- **12.2 Legal Document Review (Legal).** `legal_review` agent — local lane (local 14B for clause extraction; contracts are confidential; cloud only if Legal clears a specific model), sensitivity confidential, semantic_cache off, no tools (read/analyze only). Knowledge: `legal-playbooks` (confidential, local embeddings — clause standards, KVKK checklist, anonymized past redlines). Eval dataset ≥12 (planted risky-clause fixtures caught with citation, clean-contract false-alarm control, output schema clause/risk-level/playbook-ref validated).
  **AC:** planted-clause fixtures are all caught with a playbook citation; `make eval AGENT=legal_review` ≥ threshold; scenario card live.

## Sprint 13 — UI Usability & Automation Builder

First sprint driven by hands-on use of the finished platform rather than the backlog: the
capabilities are all built, but the web shell exposes them as eight unlabelled links, and n8n
automations can only be *run*, never *defined*, from Fleet. This sprint closes both gaps and
finally lands the System-health screen TRD §12 lists as Admin CORE (the long-deferred 7.3).

**Design decision — recipes compile to n8n, they do not replace it.** A recipe is stored in
Fleet (`automation_recipes`) as the source of truth and compiled into an n8n workflow that is
deployed over n8n's REST API. The compiler may only emit `scheduleTrigger`, `webhook`, `if`,
`set`, and `httpRequest` nodes **whose URL is Fleet's own `/v1/service/*` surface** — no free-form
URLs, no `code` nodes. That constraint is what keeps Non-Negotiable Rule 3 intact: every external
side effect still leaves through an MCP server with a declared `risk_class`, and `write:external`
steps still land in the HITL approval queue instead of executing. n8n stays the executor; the
n8n editor stays admin-only behind SSO for anything the builder deliberately cannot express.

- **13.1 Design system + app shell refresh.** Expand the 8-variable token set into a real
  light/dark system (success/warning/info/accent, surface layers, focus ring, radius/shadow
  scale — `Badge`'s `success`/`pending` variants currently reference colors that were never
  defined). Group the sidebar (Work · Automation · Knowledge · Admin) with icons and active
  state; add a top bar with page title, breadcrumb and a user/role chip. Rebuild Home from a
  flat card grid into a role-aware dashboard: pending approvals, recent automation runs, active
  agents, today's spend.
  **AC:** nav filters correctly for each of `user1`/`approver`/`builder`/`admin`; light and dark
  both legible; no color referenced that is not a defined token; all copy from i18n (TR authored
  first); Lighthouse a11y ≥ 90 on Home and Automations.
- **13.2 Explanatory layer + empty states.** A shared `PageHeader` (title + one-sentence "what
  this screen is for" + expandable "how to use it") on all eight pages; a directive empty state
  on every list (what the thing is + the first action); inline glossary for `write:external`,
  `sensitivity: pii`, `risk_class` and HITL; a "why is this waiting" line on each approval row.
  **AC:** every page has a header and an empty state; no user-facing string leaves an unexplained
  platform term; TR/EN complete with no missing-key warnings.
- **13.3 Admin → Services (closes the deferred 7.3).** New `/admin/services` over
  `GET /v1/admin/services` (MANAGE_PLATFORM): per compose service, live health probed from the
  API, its local URL, a one-sentence "what it is for", and its dev credentials — masked by
  default and revealed only on an explicit action by a `platform_admin`. Values are read from
  the environment, never committed. Also surfaces queue/worker state (arq, n8n-worker) and
  provider reachability (LiteLLM, Ollama).
  **AC:** all stack services report healthy with the stack up, and a stopped container turns its
  own card red without breaking the page; non-platform-admin roles get 403; credential values are
  **absent from the API response body** for a non-`platform_admin` caller, proven by a test.
- **13.4 Automation recipes — model, compiler, deploy API.** `automation_recipes` table
  (Alembic) + Pydantic v2 recipe schema: trigger (`schedule` cron | `manual`), an ordered step
  list, and conditional branching (`if / then / else`). Steps are drawn from a fixed action
  allowlist, each backed by a `/v1/service/*` endpoint: `pg.query` (read-only), `agent.run`,
  `slack.post`, `email.send`, `http.notify`. Compiler renders the recipe to n8n workflow JSON
  (`if` → `n8n-nodes-base.if`) and deploys it via n8n's REST API, storing the returned workflow
  id on the recipe. CRUD is MANAGE_AGENTS.
  **AC:** a schedule-triggered recipe defined through the API exists and fires in n8n; a recipe
  containing `email.send` produces an approval-queue entry instead of sending; a recipe whose
  branches both write is still gated; a crafted recipe attempting a non-Fleet URL or an unlisted
  action is rejected by the compiler (security test).
- **13.5 Builder UI + reworked Automations page.** Form-driven wizard: pick a trigger → add steps
  (fields generated from each action's schema) → add a condition → preview the compiled flow in
  plain language → save and activate. The Automations page merges the static catalog with
  user-defined recipes; each card carries run history, last status, and edit/delete.
  **AC:** a `builder` defines, saves and runs an automation end to end from the browser and sees
  the run in n8n and Langfuse; with n8n stopped the page still renders its down-state; a
  `member` can view but not edit.
- **13.6 Tests, e2e, docs, sprint close.** Unit tests for the recipe schema, compiler and RBAC;
  a testcontainers integration test covering recipe → n8n deploy → trigger; a Playwright e2e for
  the builder flow; a compiler security test against URL/action injection. TRD §12 updated in
  both layers for the Services screen and the builder.
  **AC:** `make lint && make test` green; e2e green against the compose stack; docs updated in
  original and split part together.

---

## Demo Script (15 min)
1. **Discovery framing (2')** — department map is a hypothesis; platform makes validating it cheap.
2. **Support Copilot (3')** — upload doc live → ask → cited streaming answer → thumbs-down → show it in Langfuse trace with cost.
3. **Dev Agent (4')** — mock Jira ticket → plan → approval queue → approve → real PR + Slack ping; show `agent/*` branch guardrail.
4. **Invoice automation (2')** — n8n run → OCR fields → draft in approval queue (write:external never auto-executes).
5. **KVKK lane (2')** — CV parsed by local model; gateway log shows no cloud egress for `pii`.
6. **Admin (2')** — cost dashboard, budget limit trigger, audit→trace deep-link, kill switch. Close on Phase map (TRD §15).

## Deferrable Tasks
Sprint order is the priority order; nothing in the platform core is skippable. The only tasks that may be postponed without blocking anything downstream:
- **4.5** Agent Builder v1 UI (agents configurable via seed/API meanwhile)
- **7.3** Admin system-health screen (Grafana covers it)
- **9.3** chaos-lite + garak (injection corpus in 9.2 stays mandatory)
- Scope softeners: Analytics agent charts (tables-only acceptable), Automation #2 UI polish (API path + approval required), Dev Agent live-GitHub demo (fixture mode acceptable fallback).

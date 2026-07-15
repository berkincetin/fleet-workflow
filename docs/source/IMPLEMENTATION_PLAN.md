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
- **0.3** Sandbox GitHub repo + PAT with repo scope; Slack incoming webhook; SMTP sandbox (mailpit in compose). *(first needed: 5.3–5.5)*
- **0.4** Containers reach host Ollama via host gateway (compose `extra_hosts: host.docker.internal:host-gateway`; k3d equivalent in values-dev). *(verified with a LiteLLM test call in 2.3)*

## Sprint 1 — Repo, Stack, CI, Gateway

- **1.1 Monorepo + dev stack.** Layout per CLAUDE.md; `docker-compose.dev.yml` (postgres, redis, qdrant, minio, keycloak, litellm, langfuse, **prometheus, grafana, loki, alertmanager**); Makefile targets; bootstrap README (dev setup — finalized in 10.1).
  **AC:** `make dev` boots the full stack; Keycloak realm imported from file (fleet realm, 5 test users incl. admin/builder/approver); Grafana reachable with Prometheus + Loki datasources provisioned.
- **1.2 CI + migrations + seed.** GitHub Actions: lint+typecheck+unit **+ security scans (trivy, bandit, gitleaks)** on PR per TRD §14; alembic init + first migration (users, departments, roles, audit_log); seed script with synthetic data, **including the analytics fixture warehouse views** consumed by 5.2's evals.
  **AC:** `make test` runs a passing suite in CI; security jobs pass (no high severity); `make seed` loads demo data incl. fixture views.
- **1.3 Gateway auth core.** FastAPI app factory; OIDC token validation; RBAC decorator + permission service; error model; health/readiness endpoints.
  **AC:** integration tests cover 401/403 paths.
- **1.4 Gateway cross-cutting middleware.** Audit middleware (append-only writes); OpenTelemetry wiring (trace_id in/out); Redis rate limiter; OpenAPI → generated TS client in `packages/shared`.
  **AC:** audit row written with trace_id; rate limit 429 test; traces visible in Grafana Tempo or logged exporter.
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
  **AC:** unit with FakeLLM: routing utility-vs-reasoning, interrupt fires on write:external tool, resume completes.
- **4.2 Agent registry + semantic cache.** Agent registry/config API; semantic cache (opt-in) in Redis, threshold per TRD §5.
  **AC:** cached answer path returns with badge flag; cache invalidates on KB collection update.
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
- **5.5 Dev Agent (agent #3).** Graph: ticket → plan → branch `agent/*` → PR draft → Slack notify; PR creation classified write:external ⇒ approval.
  **AC:** e2e: labeled mock ticket → pending approval → approve → PR exists on sandbox repo → Slack message; reject path cleanly cancels; all steps in one Langfuse trace. *(Fallback: may run in fixture mode if live GitHub sandbox is unavailable.)*

## Sprint 6 — n8n Automations

- **6.1 n8n queue mode.** Main + worker in compose/Helm; SSO-proxied subdomain; Fleet API key issuance/validation service (hashed, scoped, expiring per TRD §7.1) + service keys for n8n.
  **AC:** n8n reachable behind SSO proxy; a trivial workflow executes on a worker and calls the Fleet API with an issued key; a revoked key gets 401.
- **6.2 Automation #1 — weekly summary.** Cron → pg_ro via Fleet API → Slack.
  **AC:** runs end-to-end in dev.
- **6.3 Automation #2 — invoice intake.** Webhook/manual upload → OCR extract → draft entry → approval queue. Workflow JSONs exported to repo. *(UI polish is deferrable; the API path + approval flow is the required part.)*
  **AC:** invoice draft appears in approval queue with extracted fields; both workflows re-import cleanly on a fresh stack.

## Sprint 7 — Admin & Observability

- **7.1 Admin: users, models, budgets, API keys.** Users/roles screens; models (CRUD + smoke); budgets editor; API key management (issue/revoke, scopes — service from 6.1).
  **AC:** role change takes effect on next request; model add runs smoke test from UI; key revoked from UI is rejected on next request.
- **7.2 Cost dashboard, approvals, audit explorer.** Spend by dept/agent/model, burn-down, cache savings; approvals all-dept view; audit explorer (filter + Langfuse deep-link).
  **AC:** audit row deep-links to its trace; dashboard renders with seeded traffic.
- **7.3 [DEFERRABLE] Admin system-health screen.** Queues/workers/providers. Grafana suffices in the meantime.
  **AC:** health screen reflects a stopped worker within one refresh.
- **7.4 Grafana + alerting as code.** Dashboards provisioned as code; Alertmanager → Slack rules (budget, error rate, latency, queue depth, cost anomaly: dept daily spend > 3× 7-day average per TRD §5).
  **AC:** budget soft-limit triggers Slack+UI warning in a scripted test.

## Sprint 8 — KVKK Lane

- **8.1 Local-lane quality rehearsal.** Run Tesseract `tur` + local Qwen on realistic **synthetic** TR CV and invoice scans; measure extraction accuracy against the eval thresholds; select demo fixtures based on results; if below threshold, report findings and options (14b model, image preprocessing, [P2] local VLM) — decision stays with the user.
  **AC:** findings report with accuracy numbers per document type; demo fixture set chosen.
- **8.2 HR CV mini-flow (pii lane).** HR `pii` collection + CV parse task pinned to Ollama; bge-m3 embeddings.
  **AC:** integration test proves a `pii` request never reaches a cloud provider (recorded gateway targets); CV → structured profile via local model.
- **8.3 Erasure + clearance surfacing.** Erasure endpoint; retention job verified; sensitivity clearance matrix surfaced in Admin→Models.
  **AC:** erasure removes subject data, audit preserved pseudonymized.
- **8.4 PII masking verification.** Masking verified in logs/traces.
  **AC:** detected identifiers appear masked in Loki and Langfuse for a seeded PII conversation.

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
- **10.2 Docs + release.** Runbooks (restore, on-call basics); demo script (below) dry-run; screenshots/GIFs for the deck; tag v0.1.0.
  **AC:** all CI jobs green on tag; dry-run completes within 15 min.

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

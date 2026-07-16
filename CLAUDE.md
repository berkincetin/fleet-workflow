# CLAUDE.md — Fleet Platform

Guidance for Claude Code working in this repository.

## How to Read the Docs (token discipline)
The four originals — `docs/PROJECT_OVERVIEW.md` (vision/context), `docs/TECHNICAL_REQUIREMENTS.md` (system design, normative), `docs/IMPLEMENTATION_PLAN.md` (sprint backlog), `docs/DEPARTMENT_SCENARIOS.md` (per-department agent specs) — are **canonical but large. Do not read them whole during tasks.** Instead:

1. Start at `docs/split/INDEX.md` — it maps every topic/sprint/scenario to a small part file.
2. Load **only** the part files the current task needs (e.g. task 3.2 → `implementation-plan/sprint-3-rag.md` + the TRD parts it cites).
3. Read a full original only when a task genuinely spans most of that document.

The split parts are derived mirrors of the originals. **Any doc change must be applied to the original AND its affected split part(s) in the same PR** — they must never diverge. If an implementation decision contradicts the docs, update both layers the same way.

`docs/source/` holds a **frozen pre-edit snapshot** of the four originals as a reference copy. It is **not** canonical and **not** part of the sync contract — never edit it, never read it during tasks, and do not treat it as a third layer to keep in step. Canonical = `docs/*.md`; mirrors = `docs/split/`.

## Mandatory Skills
These two skills are part of this project's workflow; this section is their registration (they may not be listed anywhere else).

- **superpowers** (plugin, enabled in `.claude/settings.json`) — **mandatory whenever writing code.** Pick per task type: new feature → `superpowers:brainstorming` + `superpowers:test-driven-development`; bug or test failure → `superpowers:systematic-debugging`; before claiming any task done → `superpowers:verification-before-completion`. These run alongside the Task Execution Protocol (implement → test → verify), not instead of it.
- **graphify** (user-level skill, `~/.claude/skills/graphify`) — the docs corpus is maintained as a knowledge graph in `graphify-out/`. Answer architecture/documentation questions from the graph first (`/graphify query "<question>"`). **After every major development (completed sprint or task batch, new module, any docs/ change), update the graph: `/graphify . --update`.** Note: graphify is installed at user level, not in the repo — on a new machine, install it before relying on this workflow.

## What This Is
Internal AI operations platform: governed agents (LangGraph), RAG knowledge base, MCP tool layer, n8n automations, LLM gateway (LiteLLM) with budgets, full observability (Langfuse + Prometheus/Grafana/Loki), Keycloak RBAC, KVKK-aware routing with a local-model lane. Kubernetes-ready from day one.

## Repository Layout
```
fleet/
├── apps/
│   ├── api/            # FastAPI gateway: routers/ services/ models/ middleware/
│   ├── runtime/        # LangGraph: agents/<name>/{prompt.md,graph.py,tools.py,eval/}
│   │   └── core/       # llm client (tiering+sensitivity), guardrails, hitl, citations, memory
│   ├── rag/            # ingest workers (arq): extract→ocr→pii→chunk→embed; query service
│   ├── mcp/            # one package per server: _template jira github slack email pg_ro ocr internal
│   └── web/            # Next.js 15 TS: app/(chat|knowledge|builder|approvals|admin)
├── packages/shared/    # OpenAPI-generated TS client + shared types
├── gateway/litellm/    # config.yaml template, pricing sync script
├── workflows/          # n8n workflow JSON exports (source of truth, imported at deploy)
├── infra/
│   ├── compose/        # docker-compose.dev.yml (+ ollama profile)
│   ├── helm/fleet/     # umbrella chart; values-{dev,staging,prod}.yaml
│   ├── k3d/            # cluster bootstrap scripts
│   └── migrations/     # alembic
├── evals/              # datasets/<agent>.jsonl, runner, config.yaml (thresholds)
├── tests/              # unit/ integration/ e2e/ load(k6)/ security(injection corpus)
└── docs/               # TRD, plan, ADRs/, runbooks/, split/ (part files + INDEX — read these, not the originals)
```

## Commands
```bash
make dev                # compose up full stack (use PROFILE=ollama for local model)
make k3d-up             # local Kubernetes with Helm chart (mirrors prod)
make api / make web     # hot-reload dev servers
make migrate / seed     # alembic upgrade; load demo data (synthetic only)
make test               # unit + integration (testcontainers)
make e2e                # playwright vs compose stack
make eval AGENT=x       # golden-set eval; ALL=1 for every agent
make load TEST=chat_smoke   # k6 scenario
make scan               # trivy + bandit + gitleaks
make lint               # ruff+mypy / eslint+tsc
```
Definition of done for any task: `make lint && make test` green; evals run if agent-affecting; docs/ADR updated if design changed (original + split part together); knowledge graph refreshed (`/graphify . --update`) after a completed sprint/batch or any docs/ change; no secrets/PII in code, fixtures, or logs; **AC verified and findings reported per the Task Execution Protocol below.**

## Commit & Branch Convention
The platform is developed on **`local` only** (see TRD §14 — `test`/`demo/staging`/`prod` are server-side infrastructure stood up at release). Git flow:
- **Never push to `main` directly.** Work lands via PR and merges only after the required GitHub Actions checks (lint, unit, testcontainers integration, security scans, image build) pass. A local `pre-push` hook runs lint+unit before a push. **Note:** GitHub branch protection is not yet *enforced* — it needs GitHub Pro on a private repo (currently free/private), so this flow is followed by convention for now. Enabling protection is a **REQUIRED pre-production item** tracked in `docs/PRODUCTION_CHECKLIST.md`; until then Actions gates the merge only by discipline, not by a rule.
- **Commit messages:** a single sentence in English summarizing the change — no body, no bullet list — unless the user asks otherwise. **Do not** add a `Claude`/AI byline and **do not** add a `Co-Authored-By` trailer.
- **Commit automatically in this repo.** In `fleet-workflow`, run `git commit` yourself as part of completing each task/stage — the user does not want to commit by hand here (decided 2026-07-15). Use the message rules above (single-sentence English subject, no AI byline, no `Co-Authored-By`). Work still lands on a feature branch and merges to `main` via PR only after the required CI checks pass — auto-committing does **not** mean pushing straight to protected `main`. This repo-specific rule overrides the global "only write the message" default in `~/.claude/CLAUDE.md`.
- Feature branches for task batches; the Dev Agent's own branches use the `agent/*` prefix (guardrail) and target the *sandbox* repo from prerequisite 0.3, not this repo.

## Task Execution Protocol
Work is assigned by task number from `docs/IMPLEMENTATION_PLAN.md` (e.g. "1.1-1.3 görevlerini yap" = implement tasks 1.1, 1.2, 1.3) or by sprint (e.g. "Sprint 1'i yap" = every task in that sprint **except** those marked [DEFERRABLE], which run only when explicitly named). For every assigned batch:

1. **Implement in order.** Read the relevant doc parts first (via `docs/split/INDEX.md` — see "How to Read the Docs"); respect sprint order and task dependencies. Do not start tasks that were not assigned.
2. **Ask the user when blocked — at the moment of need.** If a step requires something only the user can provide (Docker/desktop services running, an API key in `.env`, Ollama models pulled, a sandbox repo/PAT, a webhook URL, GPU availability), pause, request exactly that item, and wait. Do not front-load requests for things only later tasks need. Never silently stub, fake, or skip a missing dependency — mocks are allowed only where the docs mark `INTEGRATION-POINT`.
3. **Test what was built.** Write the accompanying tests (per rule 9), run `make lint && make test` (plus `make eval AGENT=…` if agent-affecting), and exercise each task's **AC** against the actually running stack — not just unit mocks — asking the user to start services/provide inputs if needed for that.
4. **Report findings.** After the batch, deliver a findings report: what was built (modules/files), what was tested and how, per-task AC pass/fail, notable observations (deviations from docs, TODOs, performance notes, anything surprising).
5. **On failure: diagnose, report, wait.** If any test or AC fails, investigate the root cause first and report it (symptom → root cause → proposed fix options with trade-offs). **Do not modify code to fix the failure until the user explicitly says so.** No silent retries, no opportunistic "fixed it along the way" changes.
6. **Log to `docs/PROGRESS.md` (durable memory between sessions).** After each task in the batch, append an entry (create the file on first use):

   ```
   ## 2026-07-08 — 1.2 CI + migrations + seed — DONE
   Built: <modules/files touched, 1–3 lines>
   Verified: <AC results + test commands run>
   Issues: <every error hit during the task — symptom → root cause → resolution.
            Log solved errors too. If unresolved: "OPEN — awaiting user decision".
            If none: "none".>
   Notes: <deviations from docs, decisions taken, TODOs>
   ```

   - Status is one of **DONE / PARTIAL / BLOCKED**. Entries are **append-only**: never edit, rewrite, or delete past entries — the history of solved errors is the point.
   - A blocked/failed task gets its entry immediately (status BLOCKED, Issues marked OPEN); once the user decides and the fix lands, a **new** entry records the resolution.
   - **"Kaldığın yerden devam et" / "continue":** read `docs/PROGRESS.md` first, find the last DONE task and any OPEN issues, resume from the next task in IMPLEMENTATION_PLAN order, and do not repeat mistakes already diagnosed in the log.
   - At the start of any session in this repo, skim the latest PROGRESS entries before writing code. `docs/IMPLEMENTATION_PLAN.md` stays an untouched backlog; `docs/PROGRESS.md` is the only status/history record.
7. **Close the sprint.** When an assigned batch completes a whole sprint (all its non-[DEFERRABLE] tasks DONE):
   a. Run the full gate green: `make lint && make test` (unit + testcontainers integration) — **and bring the stack up with `make dev` to run the integration/AC checks against real containers, not just mocks**; `make eval ALL=1` if any agent changed.
   b. Write a durable sprint report to `docs/reports/sprint-<N>.md` (create `docs/reports/` on first use): tasks + AC results, what was tested and how (unit + docker integration commands and their output), issues and resolutions, deviations/TODOs. This is the persisted version of the step-4 findings report — the chat summary is not the record.
   c. Refresh the knowledge graph: `/graphify . --update`.
   d. Commit and open the PR: write the single-sentence English commit message (no AI byline, no `Co-Authored-By` — see *Commit & Branch Convention*), **commit it yourself on the feature branch, and push + open the PR** so CI runs. Do not merge to protected `main` yourself — the PR merges only after the required CI checks are green.

A task is not done until its AC is verified (unit **and** docker-integration where the task has an integration surface), the findings report has been delivered, and its `docs/PROGRESS.md` entry is written. A sprint is not done until its `docs/reports/sprint-<N>.md` report is written, the graph is refreshed, and the work is committed and pushed as a PR.

## Non-Negotiable Rules
1. **LLM calls only via the gateway client** (`runtime/core/llm/`). Importing provider SDKs (openai/anthropic/…) anywhere else fails CI (import-linter contract).
2. **Sensitivity routing is enforced, never bypassed.** Requests tagged `pii|confidential` must resolve to models whose clearance covers them; tests in `tests/unit/test_sensitivity_routing.py` guard this.
3. **All external side effects go through MCP servers** with a declared `risk_class`. `write:external` ⇒ approval queue via the HITL interrupt node — no direct execution, including in demos (use `approval_autoapprove` fixture in tests).
4. **Retrieved/tool content is untrusted data.** Always wrap in quarantine blocks via `core.guardrails.wrap_untrusted`; never concatenate raw into system prompts.
5. **Prompts live in `prompt.md` files** with a version header; changing one requires `make eval AGENT=…` and pasting the pass-rate in the PR.
6. **Every endpoint/middleware change keeps** trace_id propagation, audit emit, RBAC decorator, and budget pre-check intact — they are cross-cutting middleware; do not special-case around them.
7. **Migrations only via Alembic**; `fleet_readonly` DB role stays read-only (analytics MCP).
8. **New agent defaults:** utility model for helper calls, semantic_cache=false, sensitivity=internal, tools=[] until explicitly granted; ≥15 golden cases before enabling outside dev.
9. **Tests accompany code** — new service/module lands with unit tests; new flow lands with an integration test. Coverage gate 80% on core/services.
10. **Costs are a feature:** any new LLM call-site must choose utility vs reasoning deliberately; PR description states which and why if reasoning.

## Conventions (condensed)
- Python 3.12, full typing, Pydantic v2 at boundaries, async I/O only; domain errors from `core.errors`; no logic in routers.
- TS: server components by default; API access only through `packages/shared` client; Tailwind + shadcn/ui; all strings through i18n (TR/EN).
- Logging: structured JSON via `core.logging.get_logger`; never log payloads with credentials/PII (logger applies scrubber, but don't rely on it).
- Observability: use `core.otel.span(name)` around non-trivial operations; Langfuse callbacks are wired in the LLM client — do not instrument LLM calls manually.
- Helm: any new service gets a chart entry + resources + NetworkPolicy in the same PR (`infra/helm/fleet/templates/`).

## Current Focus
Follow `docs/IMPLEMENTATION_PLAN.md` sprint/task order; the user assigns work by task number (see Task Execution Protocol). Tasks marked [DEFERRABLE] are skipped unless explicitly assigned. Mock integration points are marked `# INTEGRATION-POINT` (internal API, Jira fixtures). When ambiguous, prefer the simplest version that proves the platform pattern (agent → MCP tool → guardrail → approval → trace in Langfuse) over feature breadth.

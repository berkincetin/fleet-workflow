# Sprint 2 Report — LLM Gateway, Model Registry, Budgets

**Completed:** 2026-07-21 · **Branch/PR:** `feat/sprint-2-gateway-budgets` (this PR).
**Method:** read the plan + cited TRD parts → TDD each code-bearing unit (test-first, watch-fail, minimal-green) → live AC verification against the compose stack → full gate green. Durable log in `docs/PROGRESS.md`.

Sprint 2 delivered tasks 2.1–2.4 (no [DEFERRABLE] tasks in this sprint). This is the governed **LLM gateway**: a LiteLLM proxy fronting a pinned model matrix, a registry that smoke-tests models on add, a client that is the single enforced entry point for every LLM call (sensitivity routing, spend metering, budgets), and the budget pre-check.

## Tasks & Acceptance Criteria

| Task | What shipped | AC result |
|---|---|---|
| **2.1** LiteLLM proxy | `gateway/litellm/config.yaml` (Day-0 pinned matrix: 9 models, per-model fallback chains, Langfuse callback); `pricing_sync.py` (pure `sync_prices` + `--check` CLI); config mounted into the compose litellm service; `make gateway-sync`/`gateway-check` | ✅ proxy **booted from the generated config**; `GET /v1/models` returned all 9 pinned models. `pricing_sync --check` → "pricing in sync", exit 0. |
| **2.2** Model registry | `models` table (§4.1 schema, migration `0002`); `registry.py` (validate→row, `evaluate_smoke`, "no cloud model cleared for pii"); `registry_probe.py` (live probe via proxy); `/v1/admin/models` CRUD (MANAGE_PLATFORM); default matrix seeded | ✅ adding a model runs the smoke test through the proxy and stores the result: reachable `utility` → `active`/`ok` with latency; unknown model → `error`/`failed` (verified live). |
| **2.3** Gateway client (`core/llm`) | `routing.py` (sensitivity enforcement + §8 redaction-downgrade), `cost.py`, `client.py` (`reasoning()`/`utility()`, spend capture, GatewayError), `transport.py` (proxy HTTP, no provider SDK), `ledger.py`, `factory.py` | ✅ unit sensitivity refusal + fallback selection; **live cloud call** (gpt-4o-mini) and **live Ollama call** (qwen2.5, routed by sensitivity=pii) both recorded in **Langfuse + spend_ledger**. |
| **2.4** Budgets | `budgets` + `spend_ledger` tables (migration `0003`, §11); `budget.py` (`evaluate_budget` 80/100 + `DbBudgetChecker` hierarchy); integrated into the client (pre-check before transport) | ✅ unit hard-stop blocks the call and bills nothing; soft-limit surfaced as `LLMResponse.budget_soft_exceeded`; DB pre-check hard-stops when period spend > limit. |

## What was tested and how

- **Unit** (`pytest tests/unit`, 62 passed, TDD): sensitivity routing incl. redaction-downgrade + pii refusal (9); cost/usage incl. cached price (5); client orchestration — tiering, refuse-before-transport, spend-on-success, GatewayError (6); client+budget hard-stop/soft-flag (4); budget decision 80/100/unlimited (9); registry build+smoke fold (6); pricing sync (5); static LiteLLM-config validation — fallback targets resolve, no cloud pii (6); factory role-derivation (3).
- **Integration** (`pytest tests/integration`, 13 passed, real containers): spend_ledger sink writes a row + budget pre-check hard-stop/unlimited (Postgres testcontainer, migration 0003); smoke-test-on-add `active`/`error` against the **live** LiteLLM proxy; plus Sprint 1's auth/middleware/migration/seed suite still green.
- **Docker/live (compose stack):** proxy boot + `/v1/models` (2.1); live cloud + Ollama calls through the client → spend_ledger rows (2.3); Langfuse `/api/public/observations` showing gpt-4o-mini + gemini-1.5-flash + qwen2.5 traces with token usage (2.3).
- **Full gate:** `make lint` exit 0 (ruff clean, web eslint clean, mypy advisory); `make test` exit 0.

## Notable issues resolved (symptom → root cause → fix)

- **SECURITY — keys in a tracked file:** real ANTHROPIC/OPENAI/GEMINI keys were pasted into `.env.example` (git-tracked) → would leak on push → moved to `.env` (gitignored), `.env.example` reset to empty placeholders. Never committed; **user advised to rotate**.
- **Invalid/exhausted provider keys:** Gemini key returned `API_KEY_INVALID`; Anthropic failing too → `utility`(Gemini)→gpt-4o-mini and `reasoning`(Claude)→gpt-4o via the **fallback chain**. Confirmed by the user as a key/limit issue, not code — the §4.4 graceful-degradation behaved exactly as designed. Left as-is (per protocol rule 5).
- **Langfuse callback disabled on first boot:** empty `LANGFUSE_PUBLIC_KEY` → added Langfuse **headless-init** (fixed dev keypair) to the compose langfuse service + matching litellm defaults; force-recreate → traces land.
- **qwen2.5 cold-start empty response:** first inference on the freshly-pulled 7B model timed out → warmed it directly on Ollama, then the client call succeeded (expected first-load latency).
- **Lint nits:** ruff ASYNC109 on `probe_model(timeout=…)` (httpx owns the timeout) → scoped `# noqa`; import-order in two files → `ruff --fix`.

## Deviations / deferrals

- **`fleet_role` on the registry:** §4.1 has no role column (roles are per-agent references in the TRD). The factory derives a tier role from the default-matrix model name (`derive_role`) so `reasoning()`/`utility()` route; superseded later by per-agent `reasoning_model`/`utility_model` (agents table, §11).
- **Budget admin CRUD UI is task 7.1**, not 2.4 — this sprint shipped the table + pure decision + async pre-check + client integration only.
- **Local model pulled this session:** the user pulled `qwen2.5:7b-instruct-q4_K_M` (~4.7GB) so the pinned local model matches the config.
- **Dev Langfuse keys** (`pk/sk-lf-fleet-dev`) are baked into compose for out-of-the-box tracing; override in `.env` for a real project.
- **mypy stays advisory:** 11 pre-existing errors in Sprint-1 `auth`/`middleware`/`rbac`; **zero** in the 10 new Sprint-2 modules.

## Cross-cutting rules honored

- **Rule 1** (LLM calls only via the gateway client): provider access is confined to `core/llm/transport.py` → the LiteLLM proxy; no provider SDK imported anywhere. `runtime/core/llm/` is the only call site.
- **Rule 2** (sensitivity routing enforced, never bypassed): `tests/unit/test_sensitivity_routing.py` guards it; enforced in `client._call` **before** any transport call; proven live (pii → local qwen2.5).
- **Rule 6** (budget pre-check intact): runs in the client before every call; hard-stop → `BudgetExceeded`, soft → response flag.
- **Rule 7** (migrations only via Alembic): `0002_models`, `0003_spend_and_budgets`; `fleet_readonly` untouched.
- **Rule 10** (costs are a feature): every call meters tokens+cost to `spend_ledger`; tiering helpers force a deliberate utility-vs-reasoning choice per call-site.

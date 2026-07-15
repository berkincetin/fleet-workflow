# Implementation Plan · Sprint 2 — LLM Gateway, Registry, Budgets

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 2 — LLM Gateway, Model Registry, Budgets

- **2.1 LiteLLM proxy.** Config template + pricing sync script.
  **AC:** proxy boots from generated config; pricing sync produces valid model prices.
- **2.2 Model registry.** `models` table + admin CRUD API + smoke-test-on-add.
  **AC:** adding a model via API triggers connectivity/capability smoke test; result stored.
- **2.3 Gateway client (`core/llm`).** Tiering helpers, sensitivity routing enforcement — including the **redaction-downgrade rule (TRD §8)** — retries/fallbacks, Langfuse callback, token/cost capture → `spend_ledger`.
  **AC:** unit: sensitivity refusal, fallback chain; live call through LiteLLM to one cloud model **and** one Ollama model recorded in Langfuse + spend_ledger.
- **2.4 Budgets.** Budgets table + pre-check middleware + 80%/100% behavior.
  **AC:** unit: budget hard-stop; soft-limit flag surfaced in response metadata.

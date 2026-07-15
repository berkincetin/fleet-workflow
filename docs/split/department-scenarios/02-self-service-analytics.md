# Department Scenarios · Self-Service Analytics — Data [Wave 0]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 2. Self-Service Analytics — Data [Wave 0]

**Objective:** Natural-language questions → governed read-only SQL over approved warehouse views; table + shown SQL back.
**Agent config:** `analytics` · reasoning: Claude Sonnet (SQL gen) · utility: Gemini Flash (intent/column mapping) · sensitivity: internal · semantic_cache: OFF (data freshness) · max_context: 8k.
**Knowledge:** `data-semantic-layer` (internal): view descriptions, column glossary, metric definitions — this is the semantic layer the SQL generator retrieves from.
**Tools:** `pg_ro.query` (read; allowlisted views only, auto-LIMIT 1000, 15s timeout, `fleet_readonly` role).
**Guardrails:** non-allowlisted table → refuse + log; DML keywords hard-blocked at MCP layer; generated SQL always displayed to user.
**Evals (≥15):** NL→SQL correctness on seeded fixture warehouse (result-set match, not string match); refusal test for `users_raw` table; ambiguous question → asks one clarifying question instead of guessing.
**Rollout:** supervised from day one (read-only ⇒ low risk); no approval queue needed.
**Metrics:** ad-hoc requests reaching DS team ↓ 50%, median time-to-answer < 2 min.

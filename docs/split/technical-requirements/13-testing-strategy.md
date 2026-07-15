# TRD · Testing Strategy (§13)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 13. Testing Strategy (from the first sprint, CI-gated)

1. **Unit** — pytest (+pytest-asyncio), vitest for web. Coverage gate: 80% on `core/*`, `services/*`. LLM calls mocked with a deterministic `FakeLLM` provider (fixture-driven), so agent graphs are unit-testable (routing, guardrails, HITL interrupts, budget errors).
2. **Integration** — testcontainers spin Postgres/Redis/Qdrant/MinIO; golden-path tests: ingest→query→cite; agent run with mocked MCP servers; approval interrupt→resume; budget hard-stop; sensitivity routing refusal.
3. **E2E** — Playwright: login (Keycloak), chat with citation, upload doc → ask → grounded answer, approval flow, admin budget edit. Runs against compose stack in CI nightly.
4. **Evaluation** — `evals/` golden sets per agent (**≥15 cases for conversational/RAG agents; ≥10 for narrow extraction-only agents** such as invoice/dealer/insights where the task surface is smaller — the per-scenario count in DEPARTMENT_SCENARIOS is authoritative and must satisfy this floor; assertions: must-contain, must-cite, JSON-schema, tool-called, judge-rubric via utility model). `make eval AGENT=x` locally; CI blocks agent-affecting PRs below threshold in `evals/config.yaml`; results pushed to Langfuse.
5. **Security** — CI every PR: trivy, bandit/semgrep; nightly: ZAP baseline vs staging, garak + custom injection corpus vs Support Copilot; secrets scanning (gitleaks).
6. **Load** — k6 scripts in `tests/load/`: `chat_smoke` (50 VU/5m), `chat_stress` (ramp→300 VU), `ingest_burst` (100 docs), `mixed_day` (chat+automations). Thresholds encode SLOs; run pre-release and after infra changes.
7. **Chaos-lite [P2]** — kill a runtime pod mid-agent-run in staging; assert resume from checkpoint.

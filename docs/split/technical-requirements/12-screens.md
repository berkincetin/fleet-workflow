# TRD · Admin & End-User Screens (§12)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 12. Admin & End-User Screens (Functional)

**End-user:** Chat (streaming, citations, feedback, cached-badge) · Knowledge (upload, collection browser, ingestion status) · My approvals · Workflow catalog (run/enable templates) [P2 — MVP: workflows managed in n8n directly].
**Builder:** Agent Builder (prompt editor w/ versions+diff, model pickers, tool allowlist, KB selection, guardrail policy, sensitivity, test-chat sandbox, eval trigger).
**Admin [CORE]:** Users & roles · API keys (issue/revoke, scopes) · Models (registry CRUD + smoke test) · **Budgets & Costs** (limits editor; dashboards: spend by dept/agent/model, burn-down, cache savings) · Guardrail policies (UI [P2] — MVP: managed via seed/config API, same pattern as agents before Agent Builder) · Approval queue (all-dept view) · Audit explorer (filter + trace link) · System health (queues, workers, provider status) · Feature flags (per-agent rollout %) [P2].

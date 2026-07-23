# TRD · Admin & End-User Screens (§12)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 12. Admin & End-User Screens (Functional)

**End-user:** Chat (streaming, citations, feedback, cached-badge) · Knowledge (upload, collection browser, ingestion status) · My approvals · Home dashboard (role-aware task cards) [CORE, Sprint 6.5] · Department hub (all 10 department scenarios; live cards deep-link, unbuilt scenarios show as "coming soon" with their target sprint) [CORE, Sprint 6.5] · Examples gallery (per-agent sample tasks from the eval datasets, "try it" actions, contribute new examples) [CORE, Sprint 6.5] · **Workflow catalog** (run/monitor real n8n automations via a Fleet API proxy — friendly cards, plain-language down-state; the n8n editor itself stays admin-only behind SSO) [CORE, Sprint 6.5 — promoted from P2].
**Builder:** Agent Builder (prompt editor w/ versions+diff, model pickers, tool allowlist, KB selection, guardrail policy, sensitivity, test-chat sandbox, eval trigger).
**Admin [CORE]:** Users & roles (Sprint 7) · API keys (issue/revoke, scopes) [Sprint 6.5] · Models (registry CRUD + smoke test) [Sprint 6.5] · **Budgets & Costs** (limits editor; dashboards: spend by dept/agent/model, burn-down, cache savings) [Sprint 7] · Guardrail policies (UI [P2] — MVP: managed via seed/config API, same pattern as agents before Agent Builder) · Approval queue (all-dept view) · Audit explorer (filter + trace link) [Sprint 7] · System health (queues, workers, provider status) · Feature flags (per-agent rollout %) [P2].

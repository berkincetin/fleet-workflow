# Implementation Plan · Sprint 7 — Admin & Observability

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 7 — Admin & Observability

- **7.1 Admin: users, models, budgets, API keys.** Users/roles screens; models (CRUD + smoke); budgets editor; API key management (issue/revoke, scopes — service from 6.1).
  **AC:** role change takes effect on next request; model add runs smoke test from UI; key revoked from UI is rejected on next request.
- **7.2 Cost dashboard, approvals, audit explorer.** Spend by dept/agent/model, burn-down, cache savings; approvals all-dept view; audit explorer (filter + Langfuse deep-link).
  **AC:** audit row deep-links to its trace; dashboard renders with seeded traffic.
- **7.3 [DEFERRABLE] Admin system-health screen.** Queues/workers/providers. Grafana suffices in the meantime.
  **AC:** health screen reflects a stopped worker within one refresh.
- **7.4 Grafana + alerting as code.** Dashboards provisioned as code; Alertmanager → Slack rules (budget, error rate, latency, queue depth, cost anomaly: dept daily spend > 3× 7-day average per TRD §5).
  **AC:** budget soft-limit triggers Slack+UI warning in a scripted test.

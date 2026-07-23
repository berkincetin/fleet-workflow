# Implementation Plan · Sprint 7 — Admin & Observability

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 7 — Admin & Observability

- **7.1 Admin: users/roles, budgets editor.** Users/roles screens; budgets editor. *(Models CRUD+smoke, and API key management shipped early in 6.5.9 — this task only adds what 6.5 didn't cover.)*
  **AC:** role change takes effect on next request.
- **7.2 Cost dashboard, approvals, audit explorer.** Spend by dept/agent/model, burn-down, cache savings; approvals all-dept view; audit explorer (filter + Langfuse deep-link).
  **AC:** audit row deep-links to its trace; dashboard renders with seeded traffic.
- **7.3 [DEFERRABLE] Admin system-health screen.** Queues/workers/providers. Grafana suffices in the meantime.
  **AC:** health screen reflects a stopped worker within one refresh.
- **7.4 Grafana + alerting as code.** Dashboards provisioned as code; Alertmanager → Slack rules (budget, error rate, latency, queue depth, cost anomaly: dept daily spend > 3× 7-day average per TRD §5).
  **AC:** budget soft-limit triggers Slack+UI warning in a scripted test.

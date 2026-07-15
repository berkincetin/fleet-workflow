# Department Scenarios · Generic Onboarding Checklist

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## Generic Onboarding Checklist (any new department, ~3–5 days)

1. **Discovery (day 1):** 2-hour workshop with the domain expert; map the process; pick ONE workflow with clear volume + pain; define a single success metric and the failure cost (this sets risk_class and rollout mode).
2. **Data (day 1–2):** create collections with `sensitivity`, `retention`, `pii_policy`; ingest 10–50 seed documents; verify PII pipeline output with the department.
3. **Tools (day 2–3):** list required actions; map to existing MCP tools; new system ⇒ new MCP server with per-tool risk_class (template in `apps/mcp/_template`). Real integration unavailable ⇒ mock behind `INTEGRATION-POINT`.
4. **Agent (day 3):** copy agent template; write `prompt.md` with the expert; pick lanes per sensitivity; **write ≥15 golden cases with the expert before enabling** — the expert defining "what good looks like" is the core Forward-Deployed act.
5. **Gate (day 4):** `make eval AGENT=x` ≥ threshold in `evals/config.yaml`; security corpus subset for any agent with tools.
6. **Pilot (day 4–5 + 2 weeks):** assist mode for ≤5 users; watch feedback score + override rate on the Agent Quality dashboard; iterate prompt (each change re-evaluated).
7. **Autonomy review:** write:internal automation only after eval history + dept_admin sign-off; write:external stays approval-gated; record the decision as an ADR.

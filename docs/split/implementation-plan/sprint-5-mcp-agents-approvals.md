# Implementation Plan · Sprint 5 — MCP, Agents #2–3, Approvals

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 5 — MCP, Agents #2–3, Approvals

- **5.1 MCP base + first servers.** MCP base package (risk_class, schemas, auth); servers: pg_ro (allowlist + auto-LIMIT + timeout), ocr, email (SMTP sandbox), internal-mock.
  **AC:** each server passes contract tests; risk_class declared per tool.
- **5.2 Analytics agent (agent #2).** Text-to-SQL over governed views (fixtures from 1.2), SQL shown, read-only role; evals (result-set match).
  **AC:** integration: business question → table + SQL; query attempt on non-allowlisted table is refused and logged.
- **5.3 Jira/GitHub/Slack MCP.** Jira (fixture-backed mock + real-config option), GitHub (sandbox repo), Slack (webhook).
  **AC:** contract tests green against mocks; GitHub sandbox smoke (branch create) works with PAT.
- **5.4 Approval queue.** Approval queue UI (context, diff, approve/edit/reject) + interrupt/resume wiring.
  **AC:** a pending write:external item can be approved (run resumes) or rejected (run cancels cleanly).
- **5.5 Dev Agent (agent #3).** Graph: ticket → plan → branch `agent/*` → PR draft → Slack notify; PR creation classified write:external ⇒ approval. Eval dataset (≥15 cases per DEPARTMENT_SCENARIOS §Dev Agent) + runner + CI gate wiring, same pattern as 4.4.
  **AC:** e2e: labeled mock ticket → pending approval → approve → PR exists on sandbox repo → Slack message; reject path cleanly cancels; all steps in one Langfuse trace; `make eval AGENT=dev_agent` ≥ threshold. *(Fallback: may run in fixture mode if live GitHub sandbox is unavailable.)*

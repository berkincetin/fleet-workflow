# Implementation Plan · Sprint 6 — n8n Automations

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 6 — n8n Automations

- **6.1 n8n queue mode.** Main + worker in compose/Helm; SSO-proxied subdomain; Fleet API key issuance/validation service (hashed, scoped, expiring per TRD §7.1) + service keys for n8n.
  **AC:** n8n reachable behind SSO proxy; a trivial workflow executes on a worker and calls the Fleet API with an issued key; a revoked key gets 401.
- **6.2 Automation #1 — weekly summary.** Cron → pg_ro via Fleet API → Slack.
  **AC:** runs end-to-end in dev.
- **6.3 Automation #2 — invoice intake.** Webhook/manual upload → OCR extract → draft entry → approval queue. Workflow JSONs exported to repo. Eval dataset (≥12 cases per DEPARTMENT_SCENARIOS §Invoice — extraction-type threshold, see §13.4) + runner wiring. *(UI polish is deferrable; the API path + approval flow is the required part.)*
  **AC:** invoice draft appears in approval queue with extracted fields; both workflows re-import cleanly on a fresh stack; `make eval AGENT=invoice_intake` ≥ threshold.

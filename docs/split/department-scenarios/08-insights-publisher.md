# Department Scenarios · Insights Publisher — Marketing [Wave 1]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 8. Insights Publisher — Marketing [Wave 1]

**Objective:** Monthly price-index report + social variants drafted automatically from warehouse data, in brand voice, published on approval.
**Agent config:** `insights_publisher` · reasoning: Claude Sonnet · utility: Gemini Flash · sensitivity: internal · semantic_cache: OFF.
**Knowledge:** `mkt-brand` (internal): brand-voice guide, past reports (style exemplars).
**Tools:** `pg_ro.query` index views (read) · `cms.publish` + `social.post` (**write:external → approval**) — INTEGRATION-POINT (mock CMS/social).
**Workflow (n8n):** cron monthly 1st 08:00 → data pull → draft → approval → publish; failure → Slack alert.
**Guardrails:** every numeric claim in the draft must match a query result attached to the approval item (grounding for numbers); TR language output.
**Evals (≥10):** numbers-match assertion vs fixture data; brand-voice rubric judge ≥ 4/5; no invented statistics test.
**Rollout:** approval-gated (public content).
**Metrics:** report production time days → hours; on-time publishing 100%.

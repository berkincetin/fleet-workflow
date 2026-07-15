# Department Scenarios · Listing Quality — Listings Ops [Wave 1]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 6. Listing Quality — Listings Operations [Wave 1]

**Objective:** Every new listing checked for photo–description consistency, plate blurring, prohibited content, price anomaly → flags with reasons into human review queue.
**Agent config:** `listing_quality` · vision: Gemini Flash · reasoning: Claude Sonnet (only on escalations) · utility: Gemini Flash · sensitivity: internal (public listing data) · semantic_cache: OFF.
**Tools:** `listings.get_new` (read) · `listings.flag` (write:internal, supervised) — both INTEGRATION-POINT (mock listing API + synthetic listing generator in demo) · `pg_ro.query` price-index view (read).
**Workflow (n8n):** new-listing webhook → agent → flag or pass; batch re-check job nightly (Batch API lane [P2]).
**Guardrails:** flag-only — the agent can never unpublish/reject a listing; every flag carries machine-readable reason codes for reviewer sorting.
**Evals (≥20):** labeled fixture set (photo+description pairs): color/model mismatch caught; blurred vs unblurred plate detection; clean listing → no flag (false-positive control ≥ 85% precision target).
**Rollout:** shadow mode 2 weeks (flags logged, not shown) → supervised.
**Metrics:** moderation throughput ↑, reviewer agreement with flags ≥ 85%, review backlog ↓.

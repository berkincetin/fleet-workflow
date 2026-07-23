# Implementation Plan · Sprint 11 — Wave 1 Scenarios

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 11 — Wave 1 Scenarios

Post-MVP onboarding of the three Wave 1 department scenarios (docs/split/department-scenarios/06-08), following the generic checklist in `department-scenarios/99-onboarding-checklist.md`. Each flips its `/scenarios` card from "coming soon" to live on completion.

- **11.1 Listing Quality (Listings Ops).** `listing_quality` agent — vision Gemini Flash, reasoning Claude Sonnet (escalations only), utility Gemini Flash, sensitivity internal, semantic_cache off. Tools: `listings.get_new`/`listings.flag` (INTEGRATION-POINT mock listing API + synthetic listing generator), `pg_ro.query` price-index view. n8n workflow: new-listing webhook → agent → flag/pass, plus nightly batch re-check job. Flag-only guardrail (agent never unpublishes). Eval dataset ≥20 (photo/description mismatch, blurred-plate detection, clean-listing false-positive control ≥85% precision).
  **AC:** shadow mode 2 weeks (flags logged, not shown) verified in a scripted run; `make eval AGENT=listing_quality` ≥ threshold; scenario card live.
- **11.2 Vehicle Intake (Trink sat!).** `vehicle_intake` agent — vision Gemini Flash (photos non-PII after plate-mask step), local OCR for expertise PDFs (owner PII) → redact → cloud reasoning on redacted brief, sensitivity confidential, no write tools. Tools: `ocr.extract` (local), `pg_ro.query` comparables/price-index views. Eval dataset ≥15 (chassis/km/damage-table extraction, price-band sanity vs fixture comparables, missing-report → "incomplete" with no invented values).
  **AC:** `make eval AGENT=vehicle_intake` ≥ threshold; missing-report fixture never invents values; scenario card live.
- **11.3 Insights Publisher (Marketing).** `insights_publisher` agent — reasoning Claude Sonnet, utility Gemini Flash, sensitivity internal, semantic_cache off. Knowledge: `mkt-brand` (brand-voice guide, past reports). Tools: `pg_ro.query` index views (read), `cms.publish`+`social.post` (**write:external → approval**, INTEGRATION-POINT mock CMS/social). n8n workflow: cron monthly 1st 08:00 → data pull → draft → approval → publish; failure → Slack alert. Guardrail: every numeric claim must match an attached query result. Eval dataset ≥10 (numbers-match assertion, brand-voice rubric judge ≥4/5, no-invented-statistics test).
  **AC:** monthly cron produces a draft with grounded numbers pending approval; `make eval AGENT=insights_publisher` ≥ threshold; scenario card live.

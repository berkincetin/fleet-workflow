# Department Scenarios · Vehicle Intake — Trink sat! [Wave 1]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 7. Vehicle Intake — Trink sat! [Wave 1]

**Objective:** Pre-assessment brief for acquisition specialists: expertise-report extraction + photo damage summary + comparables + suggested price band. Advisory only.
**Agent config:** `vehicle_intake` · vision: Gemini Flash (photos are non-PII after plate masking step) · OCR: local for expertise PDFs (contain owner PII) → redact → cloud reasoning on redacted brief · sensitivity: confidential.
**Tools:** `ocr.extract` (read, local) · `pg_ro.query` comparables + price-index views (read) · no write tools.
**Evals (≥15):** field extraction from sample expertise reports (chassis, km, damage table); price-band sanity vs fixture comparables (band must contain median of top-5 comparables); missing-report case → brief marked "incomplete", no invented values.
**Rollout:** assist permanently (human makes the offer).
**Metrics:** intake assessment time ↓ 50%, offer variance between specialists ↓.

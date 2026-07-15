# Department Scenarios · Dealer Onboarding — Corporate Sales [Wave 2]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 9. Dealer Onboarding — Corporate Sales [Wave 2]

**Objective:** Dealer application dossier check: OCR authorization certificate + tax registration, validate fields, cross-check application, request missing items by templated email, hand clean file to sales rep.
**Agent config:** `dealer_onboarding` · **pii lane** for documents (local OCR + local extraction; tax no/IBAN) · utility cloud allowed for non-PII orchestration text · sensitivity: pii.
**Tools:** `ocr.extract` (read, local) · `crm.get_application` (read, INTEGRATION-POINT) · `email.send` (**write:external → approval** initially; supervised auto-send for missing-doc template after eval history) · `crm.update_status` (write:internal).
**Evals (≥12):** field extraction on synthetic certificates; mismatch fixture (application name ≠ certificate) → flag; email template correctness (right missing items listed, TR formal tone).
**Rollout:** approval on all outbound email first month → template auto-send.
**Metrics:** onboarding cycle time ↓, incomplete-application loops ↓.

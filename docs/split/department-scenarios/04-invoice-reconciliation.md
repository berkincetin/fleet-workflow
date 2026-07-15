# Department Scenarios · Invoice & Reconciliation — Finance [Wave 0]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 4. Invoice & Reconciliation — Finance [Wave 0]

**Objective:** Invoice file → extracted fields → validation against purchase records → **draft** accounting entry in approval queue; mismatches flagged with reasons.
**Agent config:** `invoice_agent` · reasoning: Claude Sonnet (on **redacted** text) · utility: Gemini Flash · sensitivity: confidential · semantic_cache: OFF.
**Knowledge:** `fin-invoices` (confidential, pii_policy=redact, retention 7y) — IBAN/tax-no/vendor PII redacted at ingestion; originals in MinIO with restricted ACL.
**OCR path:** local (Tesseract `tur`) because raw invoices contain IBAN/tax identifiers; cloud vision only for pre-redacted or non-sensitive docs. Local VLM upgrade [P2].
**Tools:** `ocr.extract` (read, local) · `pg_ro.query` purchase-orders view (read) · `erp.create_draft_entry` (**write:external → approval**) — INTEGRATION-POINT (mock ERP in MVP).
**Workflow (n8n):** intake via upload/webhook → agent → approval queue → on approve, ERP call; on reject, Slack to submitter.
**Evals (≥12):** field extraction accuracy ≥ 95% on synthetic invoice set; mismatch fixture (amount differs from PO) → must flag, never auto-draft as clean; duplicate invoice fixture → flag.
**Rollout:** approval-gated forever (financial writes).
**Metrics:** processing time per invoice ↓ 70%, entry error rate ↓.

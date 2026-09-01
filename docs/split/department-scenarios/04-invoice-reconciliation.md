# Department Scenarios · Invoice & Reconciliation — Finance [Wave 0]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 4. Invoice & Reconciliation — Finance [Wave 0]

**Objective:** Invoice file → extracted fields → validation against purchase records → **draft** accounting entry in approval queue; mismatches flagged with reasons.
**Agent config:** `invoice_agent` · reasoning: **local Qwen** (extraction never leaves the local lane) · utility: Gemini Flash · sensitivity: confidential · semantic_cache: OFF.
> **Note (2026-09-01):** this line previously read "Claude Sonnet (on **redacted** text)". The implementation has always called `extract_invoice_fields` *without* `redacted=True`, and `core.llm.routing.select_model` gives no cloud model clearance ≥ `confidential`, so extraction has resolved to local Qwen since Sprint 6 — verified live at 100% (18/18) on the invoice eval. The doc is corrected to match the code rather than the reverse: the local lane is the *more* conservative reading of §8 (invoice text carries IBAN/tax identifiers and never reaches a cloud provider), and the redaction machinery lives in `fleet_rag.ingest.pii` while the agent lives in `fleet-runtime`, which depends the other way round — routing extraction through it would invert the package dependency. Revisit only if extraction quality proves insufficient on the local model.
**Knowledge:** `fin-invoices` (confidential, pii_policy=redact, retention 7y) — IBAN/tax-no/vendor PII redacted at ingestion; originals in MinIO with restricted ACL.
**OCR path:** local (Tesseract `tur`) because raw invoices contain IBAN/tax identifiers; cloud vision only for pre-redacted or non-sensitive docs. Local VLM upgrade [P2].
**Tools:** `ocr.extract` (read, local) · `pg_ro.query` purchase-orders view (read) · `erp.create_draft_entry` (**write:external → approval**) — INTEGRATION-POINT (mock ERP in MVP).
**Workflow (n8n):** intake via upload/webhook → agent → approval queue → on approve, ERP call; on reject, Slack to submitter.
**Evals (≥12):** field extraction accuracy ≥ 95% on synthetic invoice set; mismatch fixture (amount differs from PO) → must flag, never auto-draft as clean; duplicate invoice fixture → flag.
**Rollout:** approval-gated forever (financial writes).
**Metrics:** processing time per invoice ↓ 70%, entry error rate ↓.

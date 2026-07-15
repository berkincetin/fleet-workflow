# TRD · Privacy & KVKK (§8)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 8. Privacy & KVKK

- **Data classification [CORE]:** every collection and every agent has `sensitivity ∈ {public, internal, confidential, pii}`. Uploads inherit collection sensitivity; agents cannot read collections above their level; requests carry max(**effective** sensitivity of inputs) for routing (§4.2/§4.3).
- **PII pipeline [CORE]:** ingestion runs Presidio (+TCKN/IBAN/phone TR recognizers) → findings stored as metadata → policy per collection: `redact` (default for internal) / `block` / `allow-local-only` (pii collections). Chat inputs scanned lightweight; detected identifiers masked in logs/traces always.
- **Redaction downgrade [CORE]:** content that has passed the PII pipeline under policy `redact` (all findings removed/masked) carries **effective sensitivity `internal`** for routing purposes. This is the mechanism that permits cloud reasoning over redacted invoices and briefs (Finance, Vehicle Intake) while originals stay local-only. The original classification is preserved on the source document and in audit; redacted chunks record `redacted=true` + original sensitivity. Policies `allow-local-only` and `block` never downgrade — content under them keeps its original sensitivity end-to-end.
- **Local-model lane [CORE]:** `pii/confidential` → Ollama/vLLM models flagged `local`. Demo proves the lane end-to-end (HR CVs processed by local model while Support Copilot uses cloud).
- **Retention & erasure [CORE]:** per-collection retention days (worker purges chunks+files+vectors); `DELETE /v1/subjects/{hash}` erases a person's conversations/uploads (right to erasure); audit rows are kept but pseudonymized.
- **Residency:** all state (PG, Qdrant, MinIO, Langfuse) self-hosted in company infra; cloud LLM usage governed by clearance flags per model.

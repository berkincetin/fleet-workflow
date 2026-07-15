# Implementation Plan · Sprint 3 — RAG

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 3 — RAG

- **3.1 Ingestion pipeline.** MinIO upload API; arq worker: extract (pdf/docx/txt/img) → OCR (vision-LLM primary, tesseract fallback) → Presidio PII scan (TR recognizers) with per-collection policy → structure-aware chunking → dedup by sha → embed (utility model) → Qdrant upsert with metadata.
  **AC:** upload sample PDF + scanned image → chunks searchable; re-upload of the same doc costs 0 new embeddings.
- **3.2 Collections + retention.** Collections API with sensitivity + retention + pii_policy; retention purge job.
  **AC:** PII doc in `pii` collection gets redacted variant; purge removes expired chunks/files/vectors.
- **3.3 Query + citations.** Hybrid retrieval (dense + keyword filter), per-agent top_k/token caps, citation payloads; chat-less test harness endpoint `/v1/rag/query`.
  **AC:** e2e (API-level): question over seeded docs returns grounded answer object with citations.
- **3.4 Web shell + Knowledge UI.** Next.js shell (auth, layout, i18n) + Knowledge screens (upload, status, browse).
  **AC:** Knowledge UI shows ingestion states live.

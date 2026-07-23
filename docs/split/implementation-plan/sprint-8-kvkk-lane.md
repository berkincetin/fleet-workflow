# Implementation Plan · Sprint 8 — KVKK Lane

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 8 — KVKK Lane

- **8.1 Local-lane quality rehearsal.** Run Tesseract `tur` + local Qwen on realistic **synthetic** TR CV and invoice scans; measure extraction accuracy against the eval thresholds; select demo fixtures based on results; if below threshold, report findings and options (14b model, image preprocessing, [P2] local VLM) — decision stays with the user.
  **AC:** findings report with accuracy numbers per document type; demo fixture set chosen.
- **8.2 HR CV mini-flow (pii lane).** HR `pii` collection + CV parse task pinned to Ollama; bge-m3 embeddings. **CI note:** the "no cloud egress" assertion is split — a GPU-free unit/integration test asserts routing *targets* (which model the gateway resolves to) on GitHub-hosted runners, while the full local-model extraction eval that needs Ollama+GPU runs on a self-hosted GPU runner (or nightly, marked `@pytest.mark.gpu` and skipped on hosted runners). Local-lane evals never gate hosted-runner PR CI.
  **AC:** integration test proves a `pii` request never reaches a cloud provider (recorded gateway targets) — runs on hosted CI without GPU; CV → structured profile via local model verified on the GPU lane.
- **8.3 Erasure + clearance surfacing.** Erasure endpoint; retention job verified; sensitivity clearance matrix surfaced in Admin→Models.
  **AC:** erasure removes subject data, audit preserved pseudonymized.
- **8.4 PII masking verification.** Masking verified in logs/traces.
  **AC:** detected identifiers appear masked in Loki and Langfuse for a seeded PII conversation.
- **8.5 HR Talent & Onboarding scenario completion.** Wrap the 8.2 CV mini-flow into a full `hr_agent` per DEPARTMENT_SCENARIOS §5: role-match shortlist draft (write:internal, dept_admin approval), `hr-policies` cloud-lane Q&A alongside the `hr-cvs` pii-lane CV parse; eval dataset (≥15 cases per spec — extraction accuracy, protected-attribute schema-exclusion, onboarding Q&A grounding); flip the HR scenario card from "partial" to live in `/scenarios`.
  **AC:** `make eval AGENT=hr_agent` ≥ threshold; a synthetic CV produces a structured profile with protected attributes excluded; HR scenario card is live end-to-end from the UI.

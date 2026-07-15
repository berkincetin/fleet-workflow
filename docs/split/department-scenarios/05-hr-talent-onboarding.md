# Department Scenarios · HR Talent & Onboarding — HR [Wave 0→1]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 5. HR Talent & Onboarding — HR [Wave 0 partial → 1]

**Objective:** (a) CV → structured profile → role-match shortlist draft. (b) Employee Q&A on policies.
**Agent config:** `hr_talent` · **pii lane**: local Qwen (parse/extract) + bge-m3 embeddings; reasoning stays local for CV content · sensitivity: pii. Separate `hr_onboarding` agent: internal, cloud lane, semantic_cache ON.
**Knowledge:** `hr-cvs` (pii, retention 12mo, local-only policy — never cloud, including embeddings) · `hr-policies` (internal).
**OCR path:** local (Tesseract) for CV PDFs/images.
**Tools:** `hr.match_role` (read — scoring service over structured profiles) · shortlist output = draft visible to dept_admin only (write:internal).
**Guardrails:** match reasoning must reference only job-relevant criteria; protected-attribute fields (age, gender, photo) excluded from the structured profile at extraction — enforced by schema; erasure endpoint covers candidates.
**Evals (≥15):** extraction accuracy on **synthetic** CVs (never real ones in fixtures); schema-exclusion test (birthdate present in CV → absent in profile); onboarding Q&A grounding tests.
**Rollout:** shortlist = assist only (HR decides); Q&A supervised.
**Metrics:** screening time per role ↓ 60%, HR question tickets ↓.

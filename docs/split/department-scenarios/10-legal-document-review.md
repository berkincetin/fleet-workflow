# Department Scenarios · Legal Document Review — Legal [Wave 2]

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

## 10. Legal Document Review — Legal [Wave 2]

**Objective:** First-pass contract review against company playbooks: risky clauses, missing standard terms, KVKK-relevant sections — cited, advisory drafts for counsel.
**Agent config:** `legal_review` · **local lane** (contracts = confidential; local 14B for clause extraction; cloud only if Legal clears a specific model) · sensitivity: confidential · semantic_cache: OFF.
**Knowledge:** `legal-playbooks` (confidential, local embeddings): clause standards, KVKK checklist, past redlines (anonymized).
**Tools:** none (read/analyze only).
**Evals (≥12):** planted risky-clause fixtures (unlimited liability, missing KVKK annex) → must catch with citation; clean contract → no false alarms beyond threshold; output schema (clause, risk level, playbook reference) validated.
**Rollout:** assist permanently (advisory).
**Metrics:** first-pass review time ↓ 50%.

---

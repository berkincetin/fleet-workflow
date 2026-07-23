# Implementation Plan · Sprint 12 — Wave 2 Scenarios

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Sprint 12 — Wave 2 Scenarios

Post-MVP onboarding of the two Wave 2 department scenarios (docs/split/department-scenarios/09-10), both requiring the local KVKK lane from Sprint 8.

- **12.1 Dealer Onboarding (Corporate Sales).** `dealer_onboarding` agent — pii lane for documents (local OCR + local extraction for tax no/IBAN), cloud utility allowed for non-PII orchestration text, sensitivity pii. Tools: `ocr.extract` (local), `crm.get_application` (read, INTEGRATION-POINT), `email.send` (**write:external → approval** initially, supervised auto-send for the missing-doc template after eval history), `crm.update_status` (write:internal). Eval dataset ≥12 (certificate field extraction, name-mismatch fixture → flag, TR formal-tone email template correctness).
  **AC:** approval-gated outbound email verified for the first month's rollout mode; `make eval AGENT=dealer_onboarding` ≥ threshold; scenario card live.
- **12.2 Legal Document Review (Legal).** `legal_review` agent — local lane (local 14B for clause extraction; contracts are confidential; cloud only if Legal clears a specific model), sensitivity confidential, semantic_cache off, no tools (read/analyze only). Knowledge: `legal-playbooks` (confidential, local embeddings — clause standards, KVKK checklist, anonymized past redlines). Eval dataset ≥12 (planted risky-clause fixtures caught with citation, clean-contract false-alarm control, output schema clause/risk-level/playbook-ref validated).
  **AC:** planted-clause fixtures are all caught with a playbook citation; `make eval AGENT=legal_review` ≥ threshold; scenario card live.

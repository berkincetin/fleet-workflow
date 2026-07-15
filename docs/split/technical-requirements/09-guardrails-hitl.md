# TRD · Guardrails & Human-in-the-Loop (§9)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 9. Guardrails & Human-in-the-Loop [CORE]
(Unchanged in principle from v1, now normative.)
- Tool `risk_class`: `read` → autonomous; `write:internal` → autonomous only if agent's eval pass-rate ≥ threshold AND dept_admin enabled; `write:external` (customer email, PR, financial entry) → **always** approval queue.
- Approval queue: full context (reasoning, payload diff), approve/edit/reject, SLA timer, all decisions audited. Interrupt/resume implemented with LangGraph checkpoints.
- Output guards: JSON schema validation; RAG grounding check in two tiers — **structural [CORE]:** every RAG answer must carry ≥1 citation and every citation must resolve to a chunk actually retrieved in that run; violation → regenerate once → else the answer degrades to "I don't know + handoff" and is flagged (`guardrail_blocks_total`). **Claim-level [P2]:** utility-model judge verifies each factual claim maps to a cited chunk; runs in evals first, promoted inline only after its own false-positive rate is measured.
- **Kill switches:** per-agent `status=paused` (instant, cached 5s) and global read-only mode.

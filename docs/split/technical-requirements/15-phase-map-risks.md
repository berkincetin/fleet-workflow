# TRD · Phase Map & Risks (§15–16)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 15. Phase Map (what ships when)

| Capability | MVP sprints | P2 (mo 1–3) | P3 |
|---|---|---|---|
| Gateway, RBAC, audit, tracing, budgets, cost dash | ✔ | | |
| RAG (OCR, citations, sensitivity, retention) | ✔ | reranker, hybrid tuning | |
| Agent runtime (tiering, guardrails, HITL, kill switch) | ✔ | agent-to-agent delegation | marketplace of shared agents |
| MCP: jira, github, slack, email, pg_ro, ocr, internal-mock | ✔ | real internal APIs, Drive/Confluence | |
| n8n queue mode + 2 templates | ✔ | template library per dept | |
| Local model lane (Ollama) | ✔ | vLLM on GPU, batch lane | fine-tuned local models |
| Admin (users, models, budgets, approvals, audit, health) | ✔ | feature flags, anomaly ML | |
| Tests: unit+integration+eval+k6 smoke+SAST/deps | ✔ | ZAP/garak nightly, chaos-lite | |
| Corporate SSO federation, Vault, partitioning | | ✔ | |
| Multi-cluster / DR site | | | ✔ |

> Note: phases here are **platform capability** build stages. The department rollout phases in PROJECT_OVERVIEW §6 (Phase 0–3) follow their own timeline; "P2" above and "Phase 2" there are not the same thing.

## 16. Risks

| Risk | Mitigation |
|---|---|
| Scope creep / stalled progress | IMPLEMENTATION_PLAN sprint order = priority order; [DEFERRABLE] task markers; platform core prioritized over agent count |
| Local model quality (TR) on CPU | Use small tasks only (PII lane extraction/classification); cloud for reasoning on non-PII; GPU path designed |
| n8n license limits embedding | Separate subdomain + SSO proxy + API integration (compliant by design) |
| LiteLLM/Langfuse version churn | Pinned versions in lockfiles + weekly renovate PRs |
| Prompt injection via KB/web | §7.3 quarantine + classifier + approval for external writes + garak CI |
| Single maintainer | Everything-as-code, this doc set, CLAUDE.md; any engineer or AI assistant can resume |

# TRD · Goals, Non-Goals, Design Principles (§1)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

# Fleet — Technical Requirements & System Design Document

**Version:** 2.0 · **Status:** Build-ready
**Scope:** Complete end-to-end design of the Fleet internal AI operations platform. This document, together with `CLAUDE.md` and `IMPLEMENTATION_PLAN.md`, is the single source of truth for development. Nothing in the MVP is "to be designed later" — features are either **[CORE]** (built in the MVP sprints of IMPLEMENTATION_PLAN.md), **[P2]** (designed here, built in Phase 2), or **[P3]** (designed here, built in Phase 3).

---

## 1. Goals, Non-Goals, Design Principles

**Goals:** One platform where ~600 employees chat with governed AI agents, run automations, and where a single engineer can onboard new departments in days. Hundreds of concurrent users and hundreds of scheduled automations must be sustainable in cost, latency, and compliance (KVKK).

**Non-goals (MVP):** Mobile apps; fine-tuning infrastructure; replacing existing BI tools; multi-region deployment.

**Design principles:**
1. **Gateway-everything:** No service calls an LLM provider directly. All LLM traffic flows through the LLM Gateway (LiteLLM). All external systems are reached only via MCP servers. This is what makes cost control, audit, and KVKK routing enforceable.
2. **Everything is an API:** Agents are invocable via REST (`/v1/agents/{id}/invoke`) with API keys, so any existing company system can embed Fleet capabilities. Fleet can absorb other internal projects, not the other way around.
3. **Secure and observable by default:** authn, RBAC, tracing, cost metering, and audit are middleware — a new endpoint or agent gets them for free.
4. **Kubernetes from day one:** dev = docker compose for speed; the same images deploy to k3d (local K8s) and any real cluster via one Helm chart.
5. **Tests are not a phase:** every module ships with unit tests; integration/eval/load/security tests run in CI from the first sprint.

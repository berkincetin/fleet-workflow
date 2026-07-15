# Department Scenarios · Wave Plan Overview & Spec Template

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

# Fleet — Department Scenario Playbooks

**Version:** 1.0 · **Depends on:** platform core (TRD §1–14 [CORE] complete)
**Purpose:** Build-ready specifications for onboarding each department onto Fleet. The platform ships first (IMPLEMENTATION_PLAN.md); each scenario below is then implemented as configuration + a small amount of code (agent graph, MCP tools, workflows, evals) following the common template. Nothing here requires changing the platform core — if a scenario seems to, that is a design bug to raise first.

**How to read a spec:** every scenario uses the same fields. `Lane` = which model lane per TRD §4.2/§8 (cloud vs local-pii). `Rollout` = assist (drafts only) → supervised (write:internal with monitoring) → autonomous (only where eval history + dept_admin approval allow; write:external is never autonomous). `INTEGRATION-POINT` marks where a mock stands in for a real system.

---

## Wave Plan Overview

| # | Scenario | Department | Wave | Sensitivity | Lane | Core tech |
|---|---|---|---|---|---|---|
| 1 | Support Copilot | Customer Service | **0 (task 4.4)** | internal | cloud | RAG, semantic cache |
| 2 | Self-Service Analytics | Data | **0 (task 5.2)** | internal | cloud | text-to-SQL, pg_ro |
| 3 | Dev Agent | IT / Engineering | **0 (task 5.5)** | internal | cloud | MCP jira/github/slack, HITL |
| 4 | Invoice & Reconciliation | Finance | **0 (task 6.3)** | confidential | local OCR + cloud reasoning on redacted | OCR, n8n, approval |
| 5 | HR Talent & Onboarding | HR | **0 partial (Sprint 8) → 1** | pii / internal | local (CVs) + cloud (policies) | local lane, OCR |
| 6 | Listing Quality | Listings Ops | 1 | internal | cloud | multimodal, n8n triggers |
| 7 | Vehicle Intake | Trink sat! | 1 | confidential | mixed | multimodal, OCR, SQL |
| 8 | Insights Publisher | Marketing | 1 | internal | cloud | n8n cron, SQL, brand voice |
| 9 | Dealer Onboarding | Corporate Sales | 2 | pii | local OCR + approval emails | OCR, email MCP |
| 10 | Legal Document Review | Legal | 2 | confidential | local | RAG, clause extraction |

Wave 0 = built during the MVP sprints (task numbers reference IMPLEMENTATION_PLAN.md). Waves 1–2 = post-MVP onboarding, ~3–5 days each using the checklist at the end of this document.

---

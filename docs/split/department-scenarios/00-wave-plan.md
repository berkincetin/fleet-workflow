# Department Scenarios · Wave Plan Overview & Spec Template

<!-- Derived from docs/DEPARTMENT_SCENARIOS.md. The original is canonical.
     Any change here must also be applied to docs/DEPARTMENT_SCENARIOS.md in the same PR. -->

# Fleet — Department Scenario Playbooks

**Version:** 1.0 · **Depends on:** platform core (TRD §1–14 [CORE] complete)
**Purpose:** Build-ready specifications for onboarding each department onto Fleet. The platform ships first (IMPLEMENTATION_PLAN.md); each scenario below is then implemented as configuration + a small amount of code (agent graph, MCP tools, workflows, evals) following the common template. Nothing here requires changing the platform core — if a scenario seems to, that is a design bug to raise first.

**How to read a spec:** every scenario uses the same fields. `Lane` = which model lane per TRD §4.2/§8 (cloud vs local-pii). `Rollout` = assist (drafts only) → supervised (write:internal with monitoring) → autonomous (only where eval history + dept_admin approval allow; write:external is never autonomous). `INTEGRATION-POINT` marks where a mock stands in for a real system.

---

## Wave Plan Overview

| # | Scenario | Department | Wave | Sensitivity | Lane | Core tech | Ships when | UI status |
|---|---|---|---|---|---|---|---|---|
| 1 | Support Copilot | Customer Service | **0 (task 4.4)** | internal | cloud | RAG, semantic cache | done | live |
| 2 | Self-Service Analytics | Data | **0 (task 5.2)** | internal | cloud | text-to-SQL, pg_ro | done | live |
| 3 | Dev Agent | IT / Engineering | **0 (task 5.5)** | internal | cloud | MCP jira/github/slack, HITL | done | live |
| 4 | Invoice & Reconciliation | Finance | **0 (task 6.3)** | confidential | local OCR + local reasoning (see §4 note) | OCR, n8n, approval | done | live |
| 5 | HR Talent & Onboarding | HR | **0 partial (Sprint 8) → 1** | pii / internal | local (CVs) + cloud (policies) | local lane, OCR | task 8.5 | partial → coming soon |
| 6 | Listing Quality | Listings Ops | 1 | internal | cloud | multimodal, n8n triggers | task 11.1 | live |
| 7 | Vehicle Intake | Trink sat! | 1 | confidential | mixed | multimodal, OCR, SQL | task 11.2 | coming soon |
| 8 | Insights Publisher | Marketing | 1 | internal | cloud | n8n cron, SQL, brand voice | task 11.3 | coming soon |
| 9 | Dealer Onboarding | Corporate Sales | 2 | pii | local OCR + approval emails | OCR, email MCP | task 12.1 | coming soon |
| 10 | Legal Document Review | Legal | 2 | confidential | local | RAG, clause extraction | task 12.2 | coming soon |

Wave 0 = built during the MVP sprints (task numbers reference IMPLEMENTATION_PLAN.md). Waves 1–2 = post-MVP onboarding, ~3–5 days each using the checklist at the end of this document. "Ships when" cites the IMPLEMENTATION_PLAN.md task that flips the scenario from planned to built; "UI status" reflects the `/scenarios` department hub introduced in Sprint 6.5.

---

# Implementation Plan · Goal, Method, Task Assignment

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

# Fleet — Implementation Plan (Sprint Backlog)

**Goal:** A demoable, Kubernetes-ready platform: core (gateway, RBAC, budgets, observability, RAG, runtime, MCP, approvals, admin) + 3 department agents + 2 n8n automations + local-model KVKK lane + tests/evals/load-smoke in CI.

**Method:** AI-first development with Claude Code. Work is organized as **ordered sprints of numbered tasks** (e.g. `3.2`). There is no calendar deadline; the sprint order **is** the priority order. Tasks are executed strictly in sequence unless marked **[DEFERRABLE]**. Every completed task leaves the repo in a runnable state (`make dev` green, tests green).

**How work is assigned:** the user requests tasks by number — e.g. *"1.1-1.3 görevlerini yap"* means implement tasks 1.1, 1.2, 1.3. Execution follows the **Task Execution Protocol in CLAUDE.md**: implement → write & run tests → verify each task's AC → report findings → on any failure, diagnose and report the root cause and **wait** for the user's decision before attempting fixes.

Legend: **AC** = acceptance criteria (must be verified true when the task is reported done). **[DEFERRABLE]** = may be postponed without blocking later tasks.

---

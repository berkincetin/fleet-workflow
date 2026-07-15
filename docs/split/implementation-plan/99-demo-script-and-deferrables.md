# Implementation Plan · Demo Script & Deferrable Tasks

<!-- Derived from docs/IMPLEMENTATION_PLAN.md. The original is canonical.
     Any change here must also be applied to docs/IMPLEMENTATION_PLAN.md in the same PR. -->

## Demo Script (15 min)
1. **Discovery framing (2')** — department map is a hypothesis; platform makes validating it cheap.
2. **Support Copilot (3')** — upload doc live → ask → cited streaming answer → thumbs-down → show it in Langfuse trace with cost.
3. **Dev Agent (4')** — mock Jira ticket → plan → approval queue → approve → real PR + Slack ping; show `agent/*` branch guardrail.
4. **Invoice automation (2')** — n8n run → OCR fields → draft in approval queue (write:external never auto-executes).
5. **KVKK lane (2')** — CV parsed by local model; gateway log shows no cloud egress for `pii`.
6. **Admin (2')** — cost dashboard, budget limit trigger, audit→trace deep-link, kill switch. Close on Phase map (TRD §15).

## Deferrable Tasks
Sprint order is the priority order; nothing in the platform core is skippable. The only tasks that may be postponed without blocking anything downstream:
- **4.5** Agent Builder v1 UI (agents configurable via seed/API meanwhile)
- **7.3** Admin system-health screen (Grafana covers it)
- **9.3** chaos-lite + garak (injection corpus in 9.2 stays mandatory)
- Scope softeners: Analytics agent charts (tables-only acceptable), Automation #2 UI polish (API path + approval required), Dev Agent live-GitHub demo (fixture mode acceptable fallback).

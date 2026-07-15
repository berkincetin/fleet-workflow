# Docs Split Index — load parts, not originals

**Purpose:** the four original docs are large; reading them whole wastes tokens. This folder mirrors them as small part files. **Start here, load only the parts the current task needs.**

**Rules**
1. The originals (`docs/*.md`) are canonical. Parts are derived mirrors — never let them diverge: any doc change updates the original **and** its affected part(s) in the same PR.
2. For an assigned task `N.M`, load its sprint part + the TRD parts it cites (task text references TRD sections, e.g. "TRD §8" → `technical-requirements/08-privacy-kvkk.md`).
3. For agent/scenario work, load the scenario part + `department-scenarios/00-wave-plan.md` (spec template + wave table).
4. Read a full original only when a task genuinely spans most of that document.

## Implementation Plan (`docs/IMPLEMENTATION_PLAN.md`) — `implementation-plan/`

| Part | Contents |
|---|---|
| [00-method-and-protocol.md](implementation-plan/00-method-and-protocol.md) | Goal, method, how work is assigned, AC/[DEFERRABLE] legend |
| [sprint-0-prerequisites.md](implementation-plan/sprint-0-prerequisites.md) | 0.1–0.4 user-provided prerequisites (keys, Ollama, sandboxes) |
| [sprint-1-repo-stack-ci-gateway.md](implementation-plan/sprint-1-repo-stack-ci-gateway.md) | 1.1 dev stack+observability · 1.2 CI+security+migrations+seed · 1.3 auth core · 1.4 middleware · 1.5 Helm+k3d |
| [sprint-2-llm-gateway-budgets.md](implementation-plan/sprint-2-llm-gateway-budgets.md) | 2.1 LiteLLM · 2.2 model registry · 2.3 gateway client · 2.4 budgets |
| [sprint-3-rag.md](implementation-plan/sprint-3-rag.md) | 3.1 ingestion · 3.2 collections/retention · 3.3 query+citations · 3.4 web shell+Knowledge UI |
| [sprint-4-runtime-chat-first-agent.md](implementation-plan/sprint-4-runtime-chat-first-agent.md) | 4.1 runtime core · 4.2 registry+semantic cache · 4.3 chat UI · 4.4 Support Copilot+E2E bootstrap · 4.5 [DEFERRABLE] Agent Builder |
| [sprint-5-mcp-agents-approvals.md](implementation-plan/sprint-5-mcp-agents-approvals.md) | 5.1 MCP base · 5.2 Analytics agent · 5.3 Jira/GitHub/Slack · 5.4 approval queue · 5.5 Dev Agent |
| [sprint-6-n8n-automations.md](implementation-plan/sprint-6-n8n-automations.md) | 6.1 n8n queue mode+API keys · 6.2 weekly summary · 6.3 invoice intake |
| [sprint-7-admin-observability.md](implementation-plan/sprint-7-admin-observability.md) | 7.1 admin users/models/budgets/keys · 7.2 cost dash+audit · 7.3 [DEFERRABLE] health screen · 7.4 Grafana+alerts |
| [sprint-8-kvkk-lane.md](implementation-plan/sprint-8-kvkk-lane.md) | 8.1 local-lane rehearsal · 8.2 HR CV flow · 8.3 erasure+clearance · 8.4 PII masking |
| [sprint-9-hardening.md](implementation-plan/sprint-9-hardening.md) | 9.1 load · 9.2 security · 9.3 [DEFERRABLE] chaos+garak · 9.4 backup/restore drill |
| [sprint-10-demo-docs.md](implementation-plan/sprint-10-demo-docs.md) | 10.1 fresh-install rehearsal+README · 10.2 docs+release |
| [99-demo-script-and-deferrables.md](implementation-plan/99-demo-script-and-deferrables.md) | 15-min demo script; consolidated deferrable list |

## Technical Requirements (`docs/TECHNICAL_REQUIREMENTS.md`) — `technical-requirements/`

| Part | Contents |
|---|---|
| [01-goals-principles.md](technical-requirements/01-goals-principles.md) | §1 goals, non-goals, 5 design principles |
| [02-architecture.md](technical-requirements/02-architecture.md) | §2 high-level architecture diagram |
| [03-tech-stack.md](technical-requirements/03-tech-stack.md) | §3 decided stack table with rationale |
| [04-model-management-gateway.md](technical-requirements/04-model-management-gateway.md) | §4 model registry, default matrix, clearance rules, routing/tiering, failure behavior |
| [05-cost-token-optimization.md](technical-requirements/05-cost-token-optimization.md) | §5 budgets, spend ledger, tiering, caching, context budgeting, batch lane |
| [06-observability.md](technical-requirements/06-observability.md) | §6 trace correlation, Langfuse, Prometheus/Grafana, Loki, alerting |
| [07-security.md](technical-requirements/07-security.md) | §7 authn/RBAC matrix, platform security, OWASP LLM Top 10 mapping |
| [08-privacy-kvkk.md](technical-requirements/08-privacy-kvkk.md) | §8 data classification, PII pipeline, redaction downgrade, local lane, retention/erasure |
| [09-guardrails-hitl.md](technical-requirements/09-guardrails-hitl.md) | §9 risk_class, approval queue, grounding checks, kill switches |
| [10-scalability-capacity.md](technical-requirements/10-scalability-capacity.md) | §10 scaling, SLOs, reference sizing |
| [11-data-model.md](technical-requirements/11-data-model.md) | §11 core PostgreSQL tables |
| [12-screens.md](technical-requirements/12-screens.md) | §12 end-user/builder/admin screens |
| [13-testing-strategy.md](technical-requirements/13-testing-strategy.md) | §13 unit/integration/e2e/eval/security/load/chaos |
| [14-environments-cicd-backup.md](technical-requirements/14-environments-cicd-backup.md) | §14 environments, CI/CD pipeline, backup/DR |
| [15-phase-map-risks.md](technical-requirements/15-phase-map-risks.md) | §15 capability phase map · §16 risks |

## Department Scenarios (`docs/DEPARTMENT_SCENARIOS.md`) — `department-scenarios/`

| Part | Contents |
|---|---|
| [00-wave-plan.md](department-scenarios/00-wave-plan.md) | Wave table (who ships when), spec-field template |
| [01-support-copilot.md](department-scenarios/01-support-copilot.md) | Customer Service · Wave 0 · task 4.4 |
| [02-self-service-analytics.md](department-scenarios/02-self-service-analytics.md) | Data · Wave 0 · task 5.2 |
| [03-dev-agent.md](department-scenarios/03-dev-agent.md) | IT/Engineering · Wave 0 · task 5.5 |
| [04-invoice-reconciliation.md](department-scenarios/04-invoice-reconciliation.md) | Finance · Wave 0 · task 6.3 |
| [05-hr-talent-onboarding.md](department-scenarios/05-hr-talent-onboarding.md) | HR · Wave 0 partial (Sprint 8) → 1 · pii lane |
| [06-listing-quality.md](department-scenarios/06-listing-quality.md) | Listings Ops · Wave 1 · multimodal |
| [07-vehicle-intake.md](department-scenarios/07-vehicle-intake.md) | Trink sat! · Wave 1 · mixed lane |
| [08-insights-publisher.md](department-scenarios/08-insights-publisher.md) | Marketing · Wave 1 · n8n cron |
| [09-dealer-onboarding.md](department-scenarios/09-dealer-onboarding.md) | Corporate Sales · Wave 2 · pii lane |
| [10-legal-document-review.md](department-scenarios/10-legal-document-review.md) | Legal · Wave 2 · local lane |
| [99-onboarding-checklist.md](department-scenarios/99-onboarding-checklist.md) | Generic 3–5-day onboarding checklist for any new department |

## Project Overview (`docs/PROJECT_OVERVIEW.md`) — `project-overview/`

| Part | Contents |
|---|---|
| [01-vision-and-problem.md](project-overview/01-vision-and-problem.md) | §1–2 vision, problem statement |
| [02-platform-modules.md](project-overview/02-platform-modules.md) | §3 the five core modules |
| [03-department-use-cases.md](project-overview/03-department-use-cases.md) | §4 the ten department use cases (pain/solution/tech/metric) |
| [04-tech-map-rollout-metrics.md](project-overview/04-tech-map-rollout-metrics.md) | §5–8 tech coverage map, rollout phases 0–3, success metrics |

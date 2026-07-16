# Graph Report - .  (2026-07-16)

## Corpus Check
- 83 files · ~57,787 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 683 nodes · 882 edges · 77 communities (57 shown, 20 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 124 edges (avg confidence: 0.79)
- Token cost: 140,299 input · 6,500 output

## Community Hubs (Navigation)
- API App Factory & Audit
- OIDC Auth & JWKS
- Compose Dev Stack Services
- Web package.json Deps
- Web tsconfig
- Async DB Layer & Health
- CI Pipeline & Migrations
- ORM Models & Alembic
- App Package Skeletons
- TRD Design & Data Model
- Platform Architecture Map
- Auth Integration Tests
- Tech Stack (§3)
- shared TS Client
- CLAUDE.md & Docs Layout
- Governance: Budgets/HITL/Audit
- Department Agents
- Sprint 1 Artifacts & PROGRESS
- Sprint 2 LLM Gateway
- shared tsconfig
- Deferrable Tasks & Admin
- Sprint 0/2 Prereqs & Budgets
- MCP & Approvals (Sprint 5)
- RAG & Runtime (Sprint 3-4)
- Department Use Cases
- Demo Script & Sprint Backlog
- Sprint 1 Task Breakdown
- n8n Automations & Modules
- API Gateway & OpenAPI
- n8n & Scenario Waves
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 62
- Community 63
- Community 64
- Community 65
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 75
- Community 76

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 16 edges
2. `Fleet Technical Requirements & System Design (TRD)` - 15 edges
3. `create_app()` - 14 edges
4. `Fleet Implementation Plan (Sprint Backlog)` - 13 edges
5. `Wave Plan (department onboarding waves 0-2)` - 12 edges
6. `Department Scenarios Wave Plan & Spec Template` - 12 edges
7. `Fleet Dev Compose Stack` - 12 edges
8. `CLAUDE.md — Fleet Platform Guidance` - 11 edges
9. `Fleet Helm Umbrella Chart` - 11 edges
10. `Department Use Cases` - 10 edges

## Surprising Connections (you probably didn't know these)
- `_client()` --calls--> `create_app()`  [INFERRED]
  tests/integration/test_auth_rbac.py → apps/api/fleet_api/app.py
- `test_seed_populates_and_creates_views()` --calls--> `seed()`  [INFERRED]
  tests/integration/test_seed_runs.py → apps/api/fleet_api/seed.py
- `OpenAPI to TS client generation (@fleet/shared)` --shares_data_with--> `packages/shared (OpenAPI TS client + shared types)`  [EXTRACTED]
  docs/PROGRESS.md → CLAUDE.md
- `Shared Helm chart (per-env values)` --shares_data_with--> `infra/helm/fleet (umbrella Helm chart)`  [INFERRED]
  README.md → CLAUDE.md
- `PROGRESS entry: 1.0 (git hook + convention) + 1.1 (monorepo + dev stack) — DONE` --references--> `pre-push git hook (lint+unit)`  [EXTRACTED]
  docs/PROGRESS.md → CLAUDE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CI Pipeline: lint -> unit -> {integration, security, build-image}** — github_workflows_ci_job_lint, github_workflows_ci_job_unit, github_workflows_ci_job_integration, github_workflows_ci_job_security, github_workflows_ci_job_build_image [INFERRED 0.85]
- **Docs split-sync contract: four canonical originals kept in sync with docs/split mirror via INDEX** — docs_project_overview, docs_technical_requirements, docs_implementation_plan, docs_department_scenarios, docs_split_index, docs_split_mirrors [INFERRED 0.85]
- **Sprint 1 delivered across three stage branches merged via PRs** — feat_sprint_1_stage_a, feat_sprint_1_stage_b, feat_sprint_1_stage_c, docs_reports_sprint_1_report [INFERRED 0.85]
- **Observability Stack (Prometheus+Grafana+Loki+Alertmanager, compose)** — infra_compose_docker_compose_dev_prometheus, infra_compose_docker_compose_dev_grafana, infra_compose_docker_compose_dev_loki, infra_compose_docker_compose_dev_alertmanager [INFERRED 0.85]
- **Fleet k3d/Helm Service Stack (8 templated services)** — infra_helm_fleet_templates_postgres_postgres, infra_helm_fleet_templates_redis_redis, infra_helm_fleet_templates_qdrant_qdrant, infra_helm_fleet_templates_minio_minio, infra_helm_fleet_templates_keycloak_keycloak, infra_helm_fleet_templates_prometheus_prometheus [INFERRED 0.75]
- **Grafana Datasource Provisioning Group** — infra_compose_grafana_provisioning_datasources_datasources_prometheus_datasource, infra_compose_grafana_provisioning_datasources_datasources_loki_datasource, infra_compose_docker_compose_dev_grafana [INFERRED 0.85]
- **KVKK Sensitivity Routing Flow** — docs_technical_requirements_pii_pipeline, docs_technical_requirements_redaction_downgrade, docs_technical_requirements_sensitivity_routing, docs_technical_requirements_local_model_lane, docs_technical_requirements_clearance_rules [INFERRED 0.85]
- **Write-External Guardrail & HITL Flow** — docs_technical_requirements_risk_class, docs_technical_requirements_approval_queue, docs_project_overview_control_plane, docs_split_department_scenarios_03_dev_agent_dev_agent [INFERRED 0.75]
- **Fleet Five Core Modules** — docs_project_overview_agent_hub, docs_project_overview_workflow_studio, docs_project_overview_knowledge_base_rag, docs_project_overview_integration_layer_mcp, docs_project_overview_control_plane [EXTRACTED 1.00]
- **HITL Approval Flow (interrupt to queue to resume)** — docs_split_implementation_plan_sprint_4_runtime_chat_first_agent_hitl_interrupt_node, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_task_5_4_approval_queue, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_write_external, docs_split_project_overview_02_platform_modules_control_plane [EXTRACTED 0.90]
- **KVKK Local Model Lane (no cloud egress for pii)** — docs_split_implementation_plan_sprint_8_kvkk_lane_no_cloud_egress_guarantee, docs_split_implementation_plan_sprint_2_llm_gateway_budgets_sensitivity_routing_enforcement, docs_split_implementation_plan_sprint_0_prerequisites_task_0_2_ollama_gpu, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.85]
- **Demo Script Agent Showcase** — docs_split_implementation_plan_sprint_4_runtime_chat_first_agent_task_4_4_support_copilot, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_task_5_5_dev_agent, docs_split_implementation_plan_sprint_6_n8n_automations_task_6_3_invoice_intake, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.90]
- **Cost Governance Stack** — docs_split_technical_requirements_05_cost_token_optimization_budget_hierarchy, docs_split_technical_requirements_05_cost_token_optimization_spend_ledger, docs_split_technical_requirements_05_cost_token_optimization_cost_anomaly_alerts, docs_split_technical_requirements_03_tech_stack_litellm [EXTRACTED 0.85]
- **Guardrails & HITL Approval Flow** — docs_split_technical_requirements_09_guardrails_hitl_tool_risk_class, docs_split_technical_requirements_09_guardrails_hitl_approval_queue, docs_split_technical_requirements_03_tech_stack_langgraph, docs_split_technical_requirements_11_data_model_core_tables [EXTRACTED 0.85]
- **Agents whose write:external actions are always approval-gated** — agent_dev_agent, agent_invoice_agent, agent_insights_publisher, agent_dealer_onboarding, concept_hitl_approval_queue, concept_risk_class [EXTRACTED 1.00]

## Communities (77 total, 20 thin omitted)

### Community 0 - "API App Factory & Audit"
Cohesion: 0.07
Nodes (31): create_app(), FastAPI, FastAPI application factory., Build and configure the Fleet API application.      Set with_middleware=False, AsyncEngine, Append-only audit log writes., Insert one append-only audit row. Never updates or deletes., write_audit() (+23 more)

### Community 1 - "OIDC Auth & JWKS"
Cohesion: 0.08
Nodes (37): CurrentUser, _extract_roles(), _fetch_jwks(), get_current_user(), OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens., The authenticated principal extracted from a verified token., Verify a raw bearer token string and return the current user, or raise 401., Verify the bearer token and return the current user, or raise 401. (+29 more)

### Community 2 - "Compose Dev Stack Services"
Cohesion: 0.08
Nodes (38): Alertmanager Config (devnull route), Alertmanager Service (compose), Fleet Dev Compose Stack, Grafana Service (compose), Keycloak Service (compose), Langfuse Service (compose), LiteLLM Service (compose), Loki Service (compose) (+30 more)

### Community 3 - "Web package.json Deps"
Cohesion: 0.06
Nodes (31): dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next, @eslint/eslintrc (+23 more)

### Community 4 - "Web tsconfig"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 5 - "Async DB Layer & Health"
Cohesion: 0.11
Nodes (20): database_url(), get_engine(), AsyncEngine, Async database engine, session factory, and URL resolution for the Fleet API., Return the async database URL from FLEET_DATABASE_URL, or the local default., Create an async engine for the given URL (defaults to database_url())., Build an async session factory bound to the given engine., session_factory() (+12 more)

### Community 6 - "CI Pipeline & Migrations"
Cohesion: 0.17
Nodes (19): Alembic migration 0001_initial, apps/api/Dockerfile, .github/workflows/ci.yml, Async DB layer + ORM models (Department, User, Role, AuditLog), PROGRESS entry: 1.2 (CI + migrations + seed) — DONE, Branch feat/sprint-1-stage-b (PR #2), Required GitHub Actions checks (lint/unit/integration/security/build-image), CI job: build-image (docker build + trivy scan) (+11 more)

### Community 7 - "ORM Models & Alembic"
Cohesion: 0.16
Nodes (13): AuditLog, Base, Department, SQLAlchemy declarative models for the first migration (users, departments, roles, Declarative base for all Fleet ORM models., Role, User, DeclarativeBase (+5 more)

### Community 8 - "App Package Skeletons"
Cohesion: 0.13
Nodes (17): apps/mcp (MCP servers), apps/mcp README — MCP servers skeleton, apps/rag (ingest + query service), apps/rag README — Ingest and query service skeleton, apps/runtime (LangGraph agents), apps/runtime README — LangGraph agents skeleton, evals/ (golden datasets, runner, thresholds), Fleet Platform (internal AI operations platform) (+9 more)

### Community 9 - "TRD Design & Data Model"
Cohesion: 0.12
Nodes (16): Rollout Modes (assist/supervised/autonomous), Generic Department Onboarding Checklist, PostgreSQL Data Model, TRD Design Principles, Environments, CI/CD, Backup, Langfuse LLM Observability, Observability (Logs/Traces/Metrics), Capability Phase Map (CORE/P2/P3) (+8 more)

### Community 10 - "Platform Architecture Map"
Cohesion: 0.17
Nodes (15): Sprint 5 — MCP, Agents #2-3, Approvals, Agent Hub, Control Plane, Fleet AI Operations Platform, Integration Layer (MCP), Rollout Strategy Phases 0-3, Technology Coverage Map, Self-Service Analytics Agent (+7 more)

### Community 11 - "Auth Integration Tests"
Cohesion: 0.25
Nodes (14): MonkeyPatch, _admin_token(), backing_stack(), _client(), keycloak(), _provision_realm(), Integration test: 401 without/with a bad token, 200 with a valid member token,, Real Postgres + Redis so the audit/rate-limit middleware runs for real     inst (+6 more)

### Community 12 - "Tech Stack (§3)"
Cohesion: 0.15
Nodes (14): Everything-is-an-API Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), n8n (queue mode), RAG Service, Redis, Redis 7 + arq Workers, FastAPI / Python 3.12 (+6 more)

### Community 13 - "shared TS Client"
Cohesion: 0.14
Nodes (13): openapi-typescript, devDependencies, openapi-typescript, typescript, typescript, main, name, private (+5 more)

### Community 14 - "CLAUDE.md & Docs Layout"
Cohesion: 0.23
Nodes (12): CLAUDE.md — Fleet Platform Guidance, graphify skill, superpowers plugin skill, docs/ (TRD, plan, ADRs, runbooks, split), docs/IMPLEMENTATION_PLAN.md, docs/PROJECT_OVERVIEW.md, docs/source/ (frozen pre-edit snapshot), docs/split/INDEX.md (+4 more)

### Community 15 - "Governance: Budgets/HITL/Audit"
Cohesion: 0.18
Nodes (13): Sensitivity Clearance Ordering, Sensitivity Routing (KVKK), Budget Hierarchy, Spend Ledger, OWASP LLM Top 10 Mapping, Retention & Right to Erasure, Approval Queue (HITL), Tool Risk Class (+5 more)

### Community 16 - "Department Agents"
Cohesion: 0.21
Nodes (12): Self-Service Analytics Agent (Data), Dealer Onboarding Agent (Corporate Sales), Dev Agent (IT/Engineering), HR Talent & Onboarding Agent(s) (HR), Insights Publisher Agent (Marketing), Invoice & Reconciliation Agent (Finance), Legal Document Review Agent (Legal), Listing Quality Agent (Listings Ops) (+4 more)

### Community 17 - "Sprint 1 Artifacts & PROGRESS"
Cohesion: 0.20
Nodes (12): infra/compose/docker-compose.dev.yml (12-service stack), PROGRESS — Fleet Platform (durable append-only log), docs/PROGRESS.md, PROGRESS entry: 1.0 (git hook + convention) + 1.1 (monorepo + dev stack) — DONE, Sprint 1 Report — Repo, Stack, CI, Gateway, docs/reports/sprint-<N>.md (sprint report), Keycloak fleet realm (5 users), Makefile (dev/down/lint/test/migrate/seed/scan) (+4 more)

### Community 18 - "Sprint 2 LLM Gateway"
Cohesion: 0.21
Nodes (12): Sprint 2 — LLM Gateway, Model Registry, Budgets, Budget Hierarchy, Sensitivity Clearance Rules, Cost & Token Optimization, Default Model Matrix, LLM Gateway (LiteLLM Proxy), Model Registry, Prompt Caching (+4 more)

### Community 19 - "shared tsconfig"
Cohesion: 0.17
Nodes (11): compilerOptions, declaration, esModuleInterop, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

### Community 20 - "Deferrable Tasks & Admin"
Cohesion: 0.20
Nodes (11): Deferrable Tasks List, Agent Kill Switches, 4.5 Agent Builder v1 [DEFERRABLE], Sprint 7 — Admin & Observability, 7.1 Admin: Users, Models, Budgets, API Keys, 7.3 Admin System-Health Screen [DEFERRABLE], 7.4 Grafana + Alerting as Code, Sprint 9 — Hardening (+3 more)

### Community 21 - "Sprint 0/2 Prereqs & Budgets"
Cohesion: 0.24
Nodes (11): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.4 Container-to-Host Ollama Reachability, Sensitivity Routing Enforcement, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy, 2.2 Model Registry (+3 more)

### Community 22 - "MCP & Approvals (Sprint 5)"
Cohesion: 0.24
Nodes (11): 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue, 5.5 Dev Agent (Agent #3), write:external Approval Classification (+3 more)

### Community 23 - "RAG & Runtime (Sprint 3-4)"
Cohesion: 0.22
Nodes (11): Sprint 3 — RAG, 3.1 Ingestion Pipeline, 3.2 Collections + Retention, 3.3 Query + Citations, 3.4 Web Shell + Knowledge UI, HITL Interrupt Node, Sprint 4 — Runtime, Chat, First Agent, 4.1 Runtime Core (+3 more)

### Community 24 - "Department Use Cases"
Cohesion: 0.29
Nodes (10): Knowledge Base (RAG), Dealer Onboarding Agent (Corporate Sales), Department Use Cases, Document Review Assistant (Legal & Compliance), Invoice & Reconciliation Agent (Finance), Listing Quality Agent, Self-Service Analytics Agent (Data & Analytics), Support Copilot (Customer Service) (+2 more)

### Community 25 - "Demo Script & Sprint Backlog"
Cohesion: 0.22
Nodes (9): 15-Minute Demo Script, Sprint 0 — Prerequisites, Sprint 10 — Demo Assembly & Docs, Sprint 1 — Repo, Stack, CI, Gateway, Sprint 3 — RAG, Sprint 7 — Admin & Observability, Sprint 9 — Hardening, Fleet Implementation Plan (Sprint Backlog) (+1 more)

### Community 26 - "Sprint 1 Task Breakdown"
Cohesion: 0.28
Nodes (9): docker-compose.dev.yml Stack, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack, 1.2 CI + Migrations + Seed, 1.3 Gateway Auth Core, 1.4 Gateway Cross-Cutting Middleware, 1.5 Helm Umbrella Chart + k3d Bootstrap (+1 more)

### Community 27 - "n8n Automations & Modules"
Cohesion: 0.25
Nodes (9): 4.2 Agent Registry + Semantic Cache + Kill Switches, Sprint 6 — n8n Automations, 6.1 n8n Queue Mode + API Keys, 6.2 Automation #1 — Weekly Summary, Agent Hub, Five Core Modules, Workflow Studio (n8n), Insights Publisher (Marketing) (+1 more)

### Community 28 - "API Gateway & OpenAPI"
Cohesion: 0.29
Nodes (8): apps/api (FastAPI gateway), apps/api README — FastAPI gateway skeleton, Auth core (create_app, config, errors, health/readyz, OIDC/RBAC), gateway/litellm (LLM gateway config + pricing sync), openapi.json (dumped API schema), packages/shared README — @fleet/shared, src/schema.d.ts (generated, do not hand-edit), Task 1.3 — Gateway auth core

### Community 29 - "n8n & Scenario Waves"
Cohesion: 0.36
Nodes (8): Sprint 6 — n8n Automations, Workflow Studio (n8n), Department Scenarios Wave Plan & Spec Template, Invoice & Reconciliation Agent, Listing Quality Agent, Vehicle Intake Agent, Insights Publisher Agent, Redaction Downgrade Rule

### Community 30 - "Community 30"
Cohesion: 0.29
Nodes (8): PROGRESS entry: 1.3 (auth core) + 1.4 (middleware) + 1.5 (Helm/k3d) — DONE, Branch feat/sprint-1-stage-a, Helm umbrella chart infra/helm/fleet (8 service templates), infra/helm/fleet (umbrella Helm chart), infra/k3d (cluster bootstrap scripts), k3d bootstrap (infra/k3d/cluster.yaml, up.sh), OpenAPI to TS client generation (@fleet/shared), Task 1.5 — Helm umbrella chart + k3d

### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (8): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, Fleet AI Operations Platform, Problem Statement, Fleet Vision (single internal platform), Platform-Level Success Metrics, Why This Approach Wins

### Community 32 - "Community 32"
Cohesion: 0.29
Nodes (8): 0.2 Ollama Host-Native with GPU, No Cloud Egress Guarantee (pii lane), Sprint 8 — KVKK Lane, 8.1 Local-Lane Quality Rehearsal, 8.2 HR CV Mini-Flow (pii lane), 8.3 Erasure + Clearance Surfacing, 8.4 PII Masking Verification, Talent & Onboarding Agent (HR)

### Community 33 - "Community 33"
Cohesion: 0.38
Nodes (7): Branch protection on main, Enable branch protection on main (task 1.0 GitHub side), Commit & Branch Convention, Production / Release Checklist, docs/PRODUCTION_CHECKLIST.md, pre-push git hook (lint+unit), Task 1.0 — Git & GitHub bootstrap

### Community 34 - "Community 34"
Cohesion: 0.29
Nodes (7): Keycloak (OIDC), Web UI (Next.js/TS), Next.js 15 Frontend, AuthN/AuthZ (Keycloak OIDC + RBAC), RBAC Role Matrix, End-User Screens, E2E Tests (Playwright)

### Community 35 - "Community 35"
Cohesion: 0.29
Nodes (7): Microsoft Presidio + TR Recognizers, Embedding Dedup (content_sha256), Loki Structured Logs, Data Classification (sensitivity levels), PII Pipeline (Presidio + TR recognizers), Redaction Downgrade Rule, chunks Table

### Community 36 - "Community 36"
Cohesion: 0.29
Nodes (6): name, packageManager, private, scripts, build, lint

### Community 37 - "Community 37"
Cohesion: 0.40
Nodes (5): apps/web (Next.js 15 TS), apps/web README — Next.js frontend skeleton, Cross-cutting middleware (trace_id, audit, rate limit, OTel), packages/shared (OpenAPI TS client + shared types), Task 1.4 — Cross-cutting middleware

### Community 38 - "Community 38"
Cohesion: 0.33
Nodes (6): Dev setup bootstrap (task 10.1), Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four environments (local/test/demo-staging/prod), Shared Helm chart (per-env values), README.md — fleet-workflow

### Community 39 - "Community 39"
Cohesion: 0.53
Nodes (6): Sprint 8 — KVKK Lane, HR Talent & Onboarding Agent, Dealer Onboarding Agent, Local-Model Lane (Ollama/vLLM), Privacy & KVKK, Retention & Erasure

### Community 40 - "Community 40"
Cohesion: 0.40
Nodes (6): Gateway-Everything Principle, LLM Gateway (LiteLLM Proxy), MCP Servers, Observability Stack (Langfuse/Prometheus/Grafana/Loki), Model Registry, Agent Builder Screen

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (6): Secure and Observable by Default, Langfuse (self-hosted), Trace ID Correlation, Langfuse LLM Layer (traces/generations), Output Guards (RAG grounding check), Evaluation (golden sets)

### Community 42 - "Community 42"
Cohesion: 0.47
Nodes (6): LiteLLM Proxy, Ollama (dev local models), vLLM (prod GPU), Fallback Chains & Circuit Breaking, Local-Model Lane (pii/confidential), Reference Sizing

### Community 43 - "Community 43"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 44 - "Community 44"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 45 - "Community 45"
Cohesion: 0.50
Nodes (5): Sprint 4 — Agent Runtime, Chat, First Agent, Knowledge Base (RAG), Support Copilot Agent, Legal Document Review Agent, RAG Grounding Check

### Community 46 - "Community 46"
Cohesion: 0.40
Nodes (5): 15-Minute Demo Script, Sprint 10 — Demo Assembly & Docs, 10.1 Fresh-Install Rehearsal, 10.2 Docs + Release, 6.3 Automation #2 — Invoice Intake

### Community 47 - "Community 47"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 48 - "Community 48"
Cohesion: 0.40
Nodes (5): Security Testing (trivy/bandit/semgrep/ZAP/garak), Prometheus/Grafana Metrics, Prompt Injection Defense (quarantine blocks), Security Tests (garak/injection corpus), Risks & Mitigations

### Community 49 - "Community 49"
Cohesion: 0.40
Nodes (5): Default Model Matrix, Routing & Tiering (utility/reasoning), Model Tiering (utility vs reasoning), Prompt Caching, agents Table

### Community 52 - "Community 52"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 53 - "Community 53"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

## Ambiguous Edges - Review These
- `docs/PROJECT_OVERVIEW.md` → `docs/source/ (frozen pre-edit snapshot)`  [AMBIGUOUS]
  CLAUDE.md · relation: conceptually_related_to

## Knowledge Gaps
- **184 isolated node(s):** `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)`, `Listing Quality Agent (Listings Ops)`, `Insights Publisher Agent (Marketing)`, `Agent Hub` (+179 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `docs/PROJECT_OVERVIEW.md` and `docs/source/ (frozen pre-edit snapshot)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `create_app()` connect `API App Factory & Audit` to `OIDC Auth & JWKS`, `Auth Integration Tests`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `CLAUDE.md — Fleet Platform Guidance` connect `CLAUDE.md & Docs Layout` to `App Package Skeletons`, `Community 33`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `_client()` connect `Auth Integration Tests` to `API App Factory & Audit`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `create_app()` (e.g. with `get_settings()` and `install_error_handlers()`) actually correct?**
  _`create_app()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Generic Onboarding Checklist (new department)`, `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)` to the rest of the system?**
  _246 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `API App Factory & Audit` be split into smaller, more focused modules?**
  _Cohesion score 0.06755260243632337 - nodes in this community are weakly interconnected._
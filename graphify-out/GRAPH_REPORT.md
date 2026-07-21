# Graph Report - .  (2026-07-21)

## Corpus Check
- 49 files · ~68,469 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1023 nodes · 1430 edges · 123 communities (79 shown, 44 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 268 edges (avg confidence: 0.77)
- Token cost: 236,492 input · 0 output

## Community Hubs (Navigation)
- LLM Gateway Client
- ORM Data Model
- Budget Enforcement
- Gateway Client Factory
- FastAPI App Factory
- Web App Dependencies
- Async DB Session Layer
- Web TypeScript Config
- LiteLLM Pricing Sync
- OIDC Auth Core
- Token Cost Computation
- TRD Platform Design
- MCP Tools & Demo Script
- Sprint Backlog Overview
- Sprint 2 Gateway Tasks
- Non-Negotiable Rules
- Sprint Progress Log
- Platform Architecture
- OpenAPI TS Client Deps
- Department Agent Roster
- KVKK Routing & Spend
- API Settings Config
- Project Working Agreements
- Platform Modules & Rollout
- MCP Integration Layer
- Wave Plan & Deferrables
- Shared Package TS Config
- Sprint 2 Model Matrix
- Sprint 3 RAG Tasks
- Observability Stack
- Domain Error Model
- Cross-Cutting Middleware
- PII Lane Agents
- Sprint 0 Prerequisites
- Storage & Vector Services
- Sprint 1 Task Set
- Plan Method & Deferrables
- KVKK Local Lane
- Dev Stack & Bootstrap
- Department Use Cases
- LiteLLM Config Tests
- RBAC Permissions
- Gateway Compose Services
- Sprint 1 Auth Design
- CI Pipeline Jobs
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
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 92
- Community 93
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120

## God Nodes (most connected - your core abstractions)
1. `LLMClient` - 20 edges
2. `compilerOptions` - 16 edges
3. `BudgetStatus` - 16 edges
4. `evaluate_budget()` - 16 edges
5. `Sensitivity` - 16 edges
6. `Fleet Technical Requirements & System Design (TRD)` - 15 edges
7. `FakeTransport` - 15 edges
8. `FakeLedger` - 14 edges
9. `Fleet Implementation Plan (Sprint Backlog)` - 13 edges
10. `LLMResponse` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Rule 1: LLM calls only via gateway client` --conceptually_related_to--> `LLM Gateway (LiteLLM Proxy)`  [INFERRED]
  CLAUDE.md → docs/source/TECHNICAL_REQUIREMENTS.md
- `Rule 2: Sensitivity routing enforced` --implements--> `Sensitivity Routing (KVKK, §4.3)`  [INFERRED]
  CLAUDE.md → docs/source/TECHNICAL_REQUIREMENTS.md
- `test_seed_populates_and_creates_views()` --calls--> `seed()`  [INFERRED]
  tests/integration/test_seed_runs.py → apps/api/fleet_api/seed.py
- `test_smoke_on_add_marks_reachable_model_active()` --calls--> `ModelDraft`  [INFERRED]
  tests/integration/test_model_smoke_probe.py → apps/api/fleet_api/registry.py
- `test_smoke_on_add_marks_unknown_model_error()` --calls--> `ModelDraft`  [INFERRED]
  tests/integration/test_model_smoke_probe.py → apps/api/fleet_api/registry.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **KVKK Sensitivity Routing & Redaction Flow** — docs_source_technical_requirements_pii_pipeline, docs_source_technical_requirements_redaction_downgrade, docs_source_technical_requirements_sensitivity_routing, docs_source_technical_requirements_local_model_lane [EXTRACTED 0.90]
- **LLM Gateway Cost Governance (registry, budgets, spend ledger)** — docs_source_technical_requirements_llm_gateway, docs_source_technical_requirements_model_registry, docs_source_technical_requirements_budget_hierarchy, docs_source_technical_requirements_spend_ledger [EXTRACTED 0.85]
- **Guardrails + HITL External-Write Control** — docs_source_technical_requirements_guardrails_hitl, docs_source_technical_requirements_tool_risk_class, docs_source_technical_requirements_approval_queue, docs_source_technical_requirements_langgraph_runtime [EXTRACTED 0.85]
- **Reasoning fallback chain (cloud tier then local lane last resort)** — gateway_litellm_config_reasoning, gateway_litellm_config_reasoning_fallback_1, gateway_litellm_config_reasoning_fallback_2, gateway_litellm_config_local_reasoning [EXTRACTED 1.00]
- **Observability stack (Grafana over Prometheus + Loki, with Alertmanager)** — infra_compose_docker_compose_dev_grafana, infra_compose_docker_compose_dev_prometheus, infra_compose_docker_compose_dev_loki, infra_compose_docker_compose_dev_alertmanager [EXTRACTED 1.00]
- **Sprint 1 three-stage delivery (foundation, CI, auth/middleware/helm)** — docs_superpowers_plans_2026_07_15_sprint_1_stage_a_plan, docs_superpowers_plans_2026_07_15_sprint_1_stage_b_plan, docs_superpowers_plans_2026_07_16_sprint_1_stage_c_plan [EXTRACTED 1.00]
- **CI Pipeline: lint -> unit -> {integration, security, build-image}** — github_workflows_ci_job_lint, github_workflows_ci_job_unit, github_workflows_ci_job_integration, github_workflows_ci_job_security, github_workflows_ci_job_build_image [INFERRED 0.85]
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

## Communities (123 total, 44 thin omitted)

### Community 0 - "LLM Gateway Client"
Cohesion: 0.05
Nodes (61): BudgetChecker, _first_content(), GatewayError, Ledger, LLMClient, LLMResponse, _opt_float(), Any (+53 more)

### Community 1 - "ORM Data Model"
Cohesion: 0.06
Nodes (56): AuditLog, Base, Budget, Department, Model, SQLAlchemy declarative models for the first migration (users, departments, roles, Spend budget for a scope (TRD §5 budget hierarchy, §11)., Declarative base for all Fleet ORM models. (+48 more)

### Community 2 - "Budget Enforcement"
Cohesion: 0.07
Nodes (31): BudgetExceeded, BudgetStatus, check_budget(), DbBudgetChecker, evaluate_budget(), _period_start(), Any, async_sessionmaker (+23 more)

### Community 3 - "Gateway Client Factory"
Cohesion: 0.08
Nodes (25): annotate_roles(), build_client(), derive_role(), load_active_models(), Any, async_sessionmaker, Build a production LLMClient from settings + the model registry (task 2.3).  Loa, Map a default-matrix model name to its tier role for routing. (+17 more)

### Community 4 - "FastAPI App Factory"
Cohesion: 0.10
Nodes (26): create_app(), FastAPI application factory., Build and configure the Fleet API application.      Set with_middleware=False, main(), Dump the FastAPI OpenAPI schema to a file for TS client generation., FastAPI, MonkeyPatch, TestClient (+18 more)

### Community 5 - "Web App Dependencies"
Cohesion: 0.06
Nodes (31): dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next, @eslint/eslintrc (+23 more)

### Community 6 - "Async DB Session Layer"
Cohesion: 0.10
Nodes (24): _app_session_factory(), database_url(), get_engine(), get_session(), async_sessionmaker, AsyncSession, Async database engine, session factory, and URL resolution for the Fleet API., Return the async database URL from FLEET_DATABASE_URL, or the local default. (+16 more)

### Community 7 - "Web TypeScript Config"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 8 - "LiteLLM Pricing Sync"
Cohesion: 0.14
Nodes (22): _is_local(), _load_litellm_price_map(), main(), PriceValidationError, Any, Exception, Pricing sync for the LiteLLM proxy config (task 2.1).  Keeps the per-token input, Best-effort load of LiteLLM's canonical price map; empty if unavailable. (+14 more)

### Community 9 - "OIDC Auth Core"
Cohesion: 0.18
Nodes (16): CurrentUser, _extract_roles(), _fetch_jwks(), get_current_user(), OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens., The authenticated principal extracted from a verified token., Verify a raw bearer token string and return the current user, or raise 401., Verify the bearer token and return the current user, or raise 401. (+8 more)

### Community 10 - "Token Cost Computation"
Cohesion: 0.21
Nodes (14): compute_cost(), parse_usage(), Any, Token-usage parsing and cost computation (TRD §5).  Pure helpers: read an OpenAI, Token counts for one LLM call., Extract token counts from an OpenAI-style response body., Compute USD cost. Cached input tokens are billed at the cached price; the     re, Usage (+6 more)

### Community 11 - "TRD Platform Design"
Cohesion: 0.12
Nodes (16): Rollout Modes (assist/supervised/autonomous), Generic Department Onboarding Checklist, PostgreSQL Data Model, TRD Design Principles, Environments, CI/CD, Backup, Langfuse LLM Observability, Observability (Logs/Traces/Metrics), Capability Phase Map (CORE/P2/P3) (+8 more)

### Community 12 - "MCP Tools & Demo Script"
Cohesion: 0.16
Nodes (16): 15-Minute Demo Script, Sprint 10 — Demo Assembly & Docs, 10.2 Docs + Release, MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue (+8 more)

### Community 13 - "Sprint Backlog Overview"
Cohesion: 0.15
Nodes (15): 15-Minute Demo Script, Sprint 0 — Prerequisites, Fleet Implementation Plan (Sprint Backlog), Invoice & Reconciliation — Finance, Vehicle Intake — Trink sat!, Sprint 10 — Demo Assembly & Docs, Sprint 3 — RAG, Sprint 6 — n8n Automations (+7 more)

### Community 14 - "Sprint 2 Gateway Tasks"
Cohesion: 0.16
Nodes (15): Sprint 2 — LLM Gateway, Model Registry, Budgets, Task 2.2 — Model registry, Task 2.3 — Gateway client (core/llm), Task 2.4 — Budgets, Budget Hierarchy, Sensitivity Clearance Rules, Cost & Token Optimization, Default Model Matrix (+7 more)

### Community 15 - "Non-Negotiable Rules"
Cohesion: 0.16
Nodes (14): Rule 1: LLM calls only via gateway client, Rule 3: External side effects via MCP with risk_class, Non-Negotiable Rules, Rule 2: Sensitivity routing enforced, Rule 4: Retrieved/tool content is untrusted data, Dev Agent (IT / Engineering), Integration Layer (MCP), Approval Queue (LangGraph interrupt/resume) (+6 more)

### Community 16 - "Sprint Progress Log"
Cohesion: 0.20
Nodes (14): PROGRESS.md Status Log, Sprint 1 Stage A (1.0 git hook + 1.1 monorepo/dev stack), Sprint 1 Stage B (1.2 CI + migrations + seed), Sprint 1 Stage C (1.3 auth + 1.4 middleware + 1.5 Helm/k3d), Sprint 1 Report — Repo, Stack, CI, Gateway, Budget Hierarchy (global→dept→agent→user), Cost & Token Optimization (§5), Data Model (PostgreSQL core tables, §11) (+6 more)

### Community 17 - "Platform Architecture"
Cohesion: 0.15
Nodes (14): Everything-is-an-API Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), n8n (queue mode), RAG Service, Redis, Redis 7 + arq Workers, FastAPI / Python 3.12 (+6 more)

### Community 18 - "OpenAPI TS Client Deps"
Cohesion: 0.14
Nodes (13): openapi-typescript, devDependencies, openapi-typescript, typescript, typescript, main, name, private (+5 more)

### Community 19 - "Department Agent Roster"
Cohesion: 0.19
Nodes (12): Self-Service Analytics Agent (Data), Dealer Onboarding Agent (Corporate Sales), Dev Agent (IT/Engineering), HR Talent & Onboarding Agent(s) (HR), Insights Publisher Agent (Marketing), Invoice & Reconciliation Agent (Finance), Legal Document Review Agent (Legal), Listing Quality Agent (Listings Ops) (+4 more)

### Community 20 - "KVKK Routing & Spend"
Cohesion: 0.18
Nodes (13): Sensitivity Clearance Ordering, Sensitivity Routing (KVKK), Budget Hierarchy, Spend Ledger, OWASP LLM Top 10 Mapping, Retention & Right to Erasure, Approval Queue (HITL), Tool Risk Class (+5 more)

### Community 21 - "API Settings Config"
Cohesion: 0.21
Nodes (8): get_settings(), Application settings, loaded from the environment (pydantic-settings)., Return a fresh Settings instance (call at app creation, not import time)., Environment-driven configuration for the Fleet API., Settings, BaseSettings, Request, Response

### Community 22 - "Project Working Agreements"
Cohesion: 0.18
Nodes (12): Commit & Branch Convention, Definition of Done, Doc/Split Sync Contract, Fleet Platform (CLAUDE.md guidance), Mandatory Skills (superpowers + graphify), PROGRESS.md Durable Memory Protocol, Task Execution Protocol, Enable Branch Protection on main (pre-prod item) (+4 more)

### Community 23 - "Platform Modules & Rollout"
Cohesion: 0.24
Nodes (12): Agent Hub, Fleet AI Operations Platform, Knowledge Base (RAG), Rollout Strategy Phases 0-3, Technology Coverage Map, Workflow Studio (n8n), Department Scenarios Wave Plan & Spec Template, Support Copilot Agent (+4 more)

### Community 24 - "MCP Integration Layer"
Cohesion: 0.21
Nodes (12): Control Plane, Integration Layer (MCP), Sprint 5 — MCP, Agents #2-3, Approvals, Task 5.1 — MCP base + first servers, Self-Service Analytics Agent, Dev Agent, Approval Queue (interrupt/resume), RAG Grounding Check (+4 more)

### Community 25 - "Wave Plan & Deferrables"
Cohesion: 0.18
Nodes (12): Dev Agent — IT / Engineering, Legal Document Review — Legal, Support Copilot — Customer Service, Wave Plan Overview, Deferrable Tasks, Demo Script (15 min), Sprint 4 — Agent Runtime, Chat, First Agent, Task 4.4 — Support Copilot (agent #1) (+4 more)

### Community 26 - "Shared Package TS Config"
Cohesion: 0.17
Nodes (11): compilerOptions, declaration, esModuleInterop, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

### Community 27 - "Sprint 2 Model Matrix"
Cohesion: 0.33
Nodes (11): Sprint 2 (2.1 LiteLLM + 2.2 registry + 2.3 client + 2.4 budgets), Sprint 2 Report — LLM Gateway, Model Registry, Budgets, Talent & Onboarding Agent (HR), Default Model Matrix (§4.2), Failure Behavior & Fallbacks (§4.4), LLM Gateway (LiteLLM Proxy), Local-Model Lane (Ollama/vLLM, pii), Model Registry (§4.1) (+3 more)

### Community 28 - "Sprint 3 RAG Tasks"
Cohesion: 0.22
Nodes (11): Sprint 3 — RAG, 3.1 Ingestion Pipeline, 3.2 Collections + Retention, 3.3 Query + Citations, 3.4 Web Shell + Knowledge UI, HITL Interrupt Node, Sprint 4 — Runtime, Chat, First Agent, 4.1 Runtime Core (+3 more)

### Community 29 - "Observability Stack"
Cohesion: 0.22
Nodes (11): compose service: grafana, compose service: loki, compose service: prometheus, Grafana Loki Datasource, Grafana Prometheus Datasource, Grafana Service (Helm), Loki Service (Helm), Prometheus Service (Helm) (+3 more)

### Community 30 - "Domain Error Model"
Cohesion: 0.27
Nodes (8): AppError, ForbiddenError, install_error_handlers(), FastAPI, Domain error model and FastAPI exception handlers., Base class for domain errors mapped to HTTP responses., Register a handler that renders AppError as a structured JSON body., Exception

### Community 31 - "Cross-Cutting Middleware"
Cohesion: 0.24
Nodes (8): AuditMiddleware, RateLimitMiddleware, Cross-cutting ASGI middleware: trace-id, append-only audit, and rate limiting., Assign a trace_id per request and echo it in the response header., Write an append-only audit row for each request, carrying the trace_id., Fixed-window per-client rate limiting backed by Redis., TraceIdMiddleware, BaseHTTPMiddleware

### Community 32 - "PII Lane Agents"
Cohesion: 0.27
Nodes (10): Dealer Onboarding — Corporate Sales, HR Talent & Onboarding — HR, Sprint 8 — KVKK Lane, HR Talent & Onboarding Agent, Dealer Onboarding Agent, Local-Model Lane (Ollama/vLLM), Privacy & KVKK, Retention & Erasure (+2 more)

### Community 33 - "Sprint 0 Prerequisites"
Cohesion: 0.27
Nodes (10): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, 0.4 Container-to-Host Ollama Reachability, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy, 2.3 Gateway Client (core/llm) (+2 more)

### Community 34 - "Storage & Vector Services"
Cohesion: 0.22
Nodes (10): compose service: minio, compose service: qdrant, Fleet Helm Umbrella Chart, MinIO Service (Helm), Helm Install NOTES, Qdrant Service (Helm), Fleet Dev (k3d) Values Overrides, MinIO Values (Helm defaults) (+2 more)

### Community 35 - "Sprint 1 Task Set"
Cohesion: 0.33
Nodes (9): Sprint 1 — Repo, Stack, CI, Gateway, Task 1.2 — CI + migrations + seed, Task 1.3 — Gateway auth core, Task 1.4 — Gateway cross-cutting middleware, Task 1.5 — Helm umbrella chart skeleton + k3d bootstrap, Sprint 1 Stage B Implementation Plan, Sprint 1 Stage C Implementation Plan, Sprint 1 Foundation Design Spec (+1 more)

### Community 36 - "Plan Method & Deferrables"
Cohesion: 0.22
Nodes (9): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, Deferrable Tasks List, 4.5 Agent Builder v1 [DEFERRABLE], Sprint 7 — Admin & Observability, 7.3 Admin System-Health Screen [DEFERRABLE], 7.4 Grafana + Alerting as Code (+1 more)

### Community 37 - "KVKK Local Lane"
Cohesion: 0.25
Nodes (9): 0.2 Ollama Host-Native with GPU, Sensitivity Routing Enforcement, No Cloud Egress Guarantee (pii lane), Sprint 8 — KVKK Lane, 8.1 Local-Lane Quality Rehearsal, 8.2 HR CV Mini-Flow (pii lane), 8.3 Erasure + Clearance Surfacing, 8.4 PII Masking Verification (+1 more)

### Community 38 - "Dev Stack & Bootstrap"
Cohesion: 0.28
Nodes (9): 10.1 Fresh-Install Rehearsal, docker-compose.dev.yml Stack, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack, 1.2 CI + Migrations + Seed, 1.3 Gateway Auth Core, 1.4 Gateway Cross-Cutting Middleware (+1 more)

### Community 39 - "Department Use Cases"
Cohesion: 0.31
Nodes (9): 5.2 Analytics Agent (Agent #2), Knowledge Base (RAG), Department Use Cases, Document Review Assistant (Legal & Compliance), Listing Quality Agent, Self-Service Analytics Agent (Data & Analytics), Support Copilot (Customer Service), Vehicle Intake Agent (Trink sat!) (+1 more)

### Community 40 - "LiteLLM Config Tests"
Cohesion: 0.25
Nodes (3): _names(), Static validation of the pinned LiteLLM config (task 2.1).  Guards the shape Lit, test_all_fallback_targets_are_defined_models()

### Community 41 - "RBAC Permissions"
Cohesion: 0.32
Nodes (7): Permission, permissions_for(), Role-based access control: roles, permissions, and the enforcement dependency., Union of permissions granted by the user's roles., Dependency factory: allow the request only if the user holds `perm`., require_permission(), StrEnum

### Community 42 - "Gateway Compose Services"
Cohesion: 0.29
Nodes (8): Task 1.1 — Monorepo + dev stack, LiteLLM Langfuse success/failure callbacks, LiteLLM master_key / management API, compose service: langfuse, compose service: litellm, compose service: postgres, Postgres Service (Helm), Postgres Values (Helm defaults)

### Community 43 - "Sprint 1 Auth Design"
Cohesion: 0.25
Nodes (8): FastAPI app factory (create_app), Keycloak aud claim mismatch risk, Cross-cutting middleware (trace_id, audit, rate-limit), OIDC token validation (Keycloak JWKS RS256), RBAC permission service (TRD 7.1 matrix), compose service: redis, Redis Service (Helm), Redis Values (Helm defaults)

### Community 44 - "CI Pipeline Jobs"
Cohesion: 0.39
Nodes (8): CI job: build-image (docker build + trivy scan), CI job: integration (pytest tests/integration, testcontainers), CI job: lint (ruff + mypy), CI job: security (bandit + gitleaks), CI job: unit (pytest tests/unit), CI GitHub Actions workflow, gitleaks/gitleaks-action@v2, Trivy scan via aquasec/trivy docker image (not trivy-action)

### Community 45 - "Community 45"
Cohesion: 0.29
Nodes (7): Self-Service Analytics — Data, Analytics fixture warehouse views, Task 5.2 — Analytics agent (agent #2), Alembic first migration (0001_initial), fleet_readonly read-only DB role, GitHub Actions CI pipeline (lint/unit/integration/security/build), Seed script with analytics fixture views (fixture_sales, fixture_orders)

### Community 46 - "Community 46"
Cohesion: 0.33
Nodes (7): Task 2.1 — LiteLLM proxy, LiteLLM per-model fallback chains, local-reasoning (ollama qwen2.5:7b, pii clearance), reasoning model (claude-sonnet-4-5, internal clearance), reasoning-fallback-1 (gpt-4o), reasoning-fallback-2 (gemini-1.5-pro), Sensitivity clearance routing (no cloud model for pii)

### Community 47 - "Community 47"
Cohesion: 0.33
Nodes (7): Self-Service Analytics Agent (Text-to-SQL), Design Principles (gateway-everything, K8s-from-day-one), High-Level Architecture, LangGraph Agent Runtime (Postgres checkpointer), Qdrant Vector DB, Technology Stack (Decided), Fleet Technical Requirements & System Design

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (7): Agent Kill Switches, 4.2 Agent Registry + Semantic Cache + Kill Switches, Sprint 9 — Hardening, 9.1 Load Testing (k6), 9.3 Chaos-Lite + garak [DEFERRABLE], 9.4 Backup & Restore Drill, Agent Hub

### Community 49 - "Community 49"
Cohesion: 0.29
Nodes (7): Fleet AI Operations Platform, Problem Statement, Fleet Vision (single internal platform), Five Core Modules, Workflow Studio (n8n), Technology Coverage Map, Why This Approach Wins

### Community 50 - "Community 50"
Cohesion: 0.29
Nodes (7): Keycloak (OIDC), Web UI (Next.js/TS), Next.js 15 Frontend, AuthN/AuthZ (Keycloak OIDC + RBAC), RBAC Role Matrix, End-User Screens, E2E Tests (Playwright)

### Community 51 - "Community 51"
Cohesion: 0.29
Nodes (7): Microsoft Presidio + TR Recognizers, Embedding Dedup (content_sha256), Loki Structured Logs, Data Classification (sensitivity levels), PII Pipeline (Presidio + TR recognizers), Redaction Downgrade Rule, chunks Table

### Community 52 - "Community 52"
Cohesion: 0.29
Nodes (7): Keycloak fleet realm with five test users, Sprint 1 Stage A Implementation Plan, pre-push git hook (task 1.0), Helm umbrella chart + k3d bootstrap, compose service: keycloak, Keycloak Service (Helm), Keycloak Values (Helm defaults)

### Community 53 - "Community 53"
Cohesion: 0.29
Nodes (6): name, packageManager, private, scripts, build, lint

### Community 54 - "Community 54"
Cohesion: 0.33
Nodes (5): configure_tracing(), new_trace_id(), OpenTelemetry setup (dev: logging exporter) and trace-id helpers., Install a console span exporter once (dev default per plan/TRD §14)., Generate a request trace id.

### Community 55 - "Community 55"
Cohesion: 0.33
Nodes (6): Dev setup bootstrap (task 10.1), Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four environments (local/test/demo-staging/prod), Shared Helm chart (per-env values), README.md — fleet-workflow

### Community 56 - "Community 56"
Cohesion: 0.33
Nodes (6): Agent Hub, Control Plane (guardrails, HITL, eval, audit), Fleet — AI Operations Platform (Overview), Knowledge Base (RAG), Support Copilot (Customer Service agent), Workflow Studio (n8n)

### Community 57 - "Community 57"
Cohesion: 0.40
Nodes (6): 2.2 Model Registry, Sprint 6 — n8n Automations, 6.1 n8n Queue Mode + API Keys, 6.2 Automation #1 — Weekly Summary, 7.1 Admin: Users, Models, Budgets, API Keys, Insights Publisher (Marketing)

### Community 58 - "Community 58"
Cohesion: 0.40
Nodes (6): Gateway-Everything Principle, LLM Gateway (LiteLLM Proxy), MCP Servers, Observability Stack (Langfuse/Prometheus/Grafana/Loki), Model Registry, Agent Builder Screen

### Community 59 - "Community 59"
Cohesion: 0.33
Nodes (6): Secure and Observable by Default, Langfuse (self-hosted), Trace ID Correlation, Langfuse LLM Layer (traces/generations), Output Guards (RAG grounding check), Evaluation (golden sets)

### Community 60 - "Community 60"
Cohesion: 0.47
Nodes (6): LiteLLM Proxy, Ollama (dev local models), vLLM (prod GPU), Fallback Chains & Circuit Breaking, Local-Model Lane (pii/confidential), Reference Sizing

### Community 61 - "Community 61"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 62 - "Community 62"
Cohesion: 0.40
Nodes (4): AsyncEngine, Append-only audit log writes., Insert one append-only audit row. Never updates or deletes., write_audit()

### Community 63 - "Community 63"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 64 - "Community 64"
Cohesion: 0.50
Nodes (5): Invoice & Reconciliation Agent (Finance), Vehicle Intake Agent (Trink sat!), PII Pipeline (Presidio + TR recognizers), Privacy & KVKK (§8), Redaction Downgrade Rule (§8)

### Community 65 - "Community 65"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 66 - "Community 66"
Cohesion: 0.40
Nodes (5): Security Testing (trivy/bandit/semgrep/ZAP/garak), Prometheus/Grafana Metrics, Prompt Injection Defense (quarantine blocks), Security Tests (garak/injection corpus), Risks & Mitigations

### Community 67 - "Community 67"
Cohesion: 0.40
Nodes (5): Default Model Matrix, Routing & Tiering (utility/reasoning), Model Tiering (utility vs reasoning), Prompt Caching, agents Table

### Community 70 - "Community 70"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 71 - "Community 71"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

### Community 76 - "Community 76"
Cohesion: 1.00
Nodes (3): openapi.json (dumped API schema), packages/shared README — @fleet/shared, src/schema.d.ts (generated, do not hand-edit)

## Ambiguous Edges - Review These
- `Self-Service Analytics Agent (Text-to-SQL)` → `Qdrant Vector DB`  [AMBIGUOUS]
  docs/source/PROJECT_OVERVIEW.md · relation: conceptually_related_to

## Knowledge Gaps
- **212 isolated node(s):** `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)`, `Listing Quality Agent (Listings Ops)`, `Insights Publisher Agent (Marketing)`, `Agent Hub` (+207 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **44 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Self-Service Analytics Agent (Text-to-SQL)` and `Qdrant Vector DB`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `BudgetStatus` connect `Budget Enforcement` to `LLM Gateway Client`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `check_budget()` connect `Budget Enforcement` to `Async DB Session Layer`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `session_factory()` connect `Async DB Session Layer` to `Budget Enforcement`, `Gateway Client Factory`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `LLMClient` (e.g. with `BudgetStatus` and `Sensitivity`) actually correct?**
  _`LLMClient` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `BudgetStatus` (e.g. with `BudgetChecker` and `GatewayError`) actually correct?**
  _`BudgetStatus` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `evaluate_budget()` (e.g. with `test_at_hard_limit_is_blocked()` and `test_at_soft_limit_sets_soft_flag_but_still_allowed()`) actually correct?**
  _`evaluate_budget()` has 12 INFERRED edges - model-reasoned connections that need verification._
# Graph Report - .  (2026-07-22)

## Corpus Check
- 115 files · ~113,736 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1891 nodes · 3203 edges · 184 communities (124 shown, 60 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 657 edges (avg confidence: 0.72)
- Token cost: 86,023 input · 0 output

## Community Hubs (Navigation)
- RAG Query & Citations
- Retention Purge Job
- Document Upload & Chunking
- Audit Logging
- MinIO Object Store
- Web Shell Layout & Auth Routes
- Model Registry
- OCR Pipeline
- Collections API & Knowledge UI
- OIDC Token Verification
- PII Detection (Presidio)
- Gateway Client Factory
- Web TS Config
- Gateway Client Embeddings
- LiteLLM Pricing Sync
- Budget Enforcement
- Gateway Client Error Handling
- Sensitivity Routing
- Text Extraction (PDF/DOCX)
- FastAPI App Factory
- Department Agent Scenarios
- Shared TS Client Deps
- LLM Cost Computation
- Sprint 2 Plan (Source)
- TRD Core Concepts (Split)
- API Settings
- ORM Core Models
- Document ORM & Router
- Gateway Client Tests
- Web Runtime Deps
- Web Dev Deps
- Auth RBAC Integration Test
- Collection ORM & Router
- Sprint 5 MCP Plan (Split)
- Architecture Overview (Split)
- Department Agent Registry
- Budget Unit Tests
- CLAUDE.md Non-Negotiable Rules
- Sensitivity Clearance Rules
- Model Gateway + Cost TRD (Split)
- Project Overview: Platform
- Sprint 5/6 Plan + RAG Overview
- Shared Package TS Config
- Observability Provisioning
- Web Package Scripts
- Gateway Client Rule + Architecture
- Sprint 4 Runtime Plan (Split)
- Compose Infra (MinIO/Qdrant/Helm)
- Production Checklist & CI
- Department Scenarios (Split)
- Sprint 3/6 Plan (Source)
- Sprint 1 Plan (Source)
- KVKK Local Lane Plan
- Sprint 1/10 Plan (Split)
- Sprint 2/6/7 Plan (Split)
- LiteLLM Config Tests
- Implementation Plan Method
- Demo Script & Sprint 9/10 Plan
- Sprint 0/2 Prerequisites
- Sprint 1 Stage C Design Notes
- GitHub Actions CI Jobs
- Gateway Client + Ledger
- Guardrails & Approval Queue
- Analytics Agent + Migrations
- Compose Core Services
- Web/Auth Architecture (Split)
- Privacy & KVKK Pipeline (Split)
- Sprint 1 Stage A + Keycloak Compose
- Root Package Config
- CLAUDE.md Protocol Rules
- K8s/Helm Foundations
- Project Overview: Control Plane
- Cost Optimization TRD (Source)
- Sprint 3 RAG Plan (Split)
- Gateway Architecture (Split)
- Observability & Guardrails (Split)
- Local Model Lane (Split)
- Shared OpenAPI Schema
- RAG Query Live Test
- Web ESLint Config
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
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
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 147
- Community 148
- Community 150
- Community 151
- Community 155
- Community 156
- HTTP Method Constants
- Web Frontend Skeleton README
- SQLAlchemy Async Session Factory
- SQLAlchemy Async Session
- Pydantic BaseModel
- Insights Publisher Scenario (Marketing)
- Listing Quality Scenario (Listings Ops)
- Sprint 0 Prerequisites
- Dealer Onboarding Scenario (Corporate Sales)
- Document Review Scenario (Legal)
- Insights Publisher Overview
- Listing Quality Agent (Multimodal)
- Rollout Strategy Phases
- Capability Phase Map
- Scalability & Capacity Planning
- Data Plane Services
- OCR Pipeline (Vision LLM + Tesseract)
- Context Budgeting Strategy
- Application & Platform Security
- Kill Switches (Agent Pause + Read-Only)
- Generated TypeScript API Client
- Alertmanager Config
- Mailpit Compose Service
- Loki Log Storage Config
- Generic Protocol Type

## God Nodes (most connected - your core abstractions)
1. `KillSwitch` - 46 edges
2. `Hit` - 38 edges
3. `AgentQueryConfig` - 30 edges
4. `LLMClient` - 30 edges
5. `Settings` - 29 edges
6. `FakeTransport` - 26 edges
7. `Agent` - 24 edges
8. `FakeLedger` - 23 edges
9. `Collection` - 22 edges
10. `run_ingestion()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Rule 1: LLM calls only via gateway client` --conceptually_related_to--> `LLM Gateway (LiteLLM Proxy)`  [INFERRED]
  CLAUDE.md → docs/source/TECHNICAL_REQUIREMENTS.md
- `Per-model fallback chains` --semantically_similar_to--> `Security: API keys leaked into tracked .env.example`  [INFERRED] [semantically similar]
  gateway/litellm/config.yaml → docs/reports/sprint-2.md
- `_qdrant_up()` --calls--> `qdrant_client_from_env()`  [INFERRED]
  tests/integration/test_rag_stores_live.py → apps/rag/fleet_rag/store/qdrant_store.py
- `test_collection_name_namespaces_by_fleet_collection_id()` --calls--> `collection_name()`  [INFERRED]
  tests/unit/test_rag_qdrant_store.py → apps/rag/fleet_rag/store/qdrant_store.py
- `test_smoke_on_add_marks_reachable_model_active()` --calls--> `ModelDraft`  [INFERRED]
  tests/integration/test_model_smoke_probe.py → apps/api/fleet_api/registry.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Support Copilot demo KB fixtures ingested and evaluated together** — docs_reports_sprint_4_md_support_copilot_agent, evals_fixtures_support_copilot_listing_quality_sop_txt, evals_fixtures_support_copilot_membership_and_payments_txt, evals_fixtures_support_copilot_trink_sat_process_txt, evals_config_support_copilot [INFERRED 0.90]
- **Nightly workflow, sprint 4 report, and Support Copilot eval config form the CI verification chain for the demo path** — github_workflows_nightly_yml, docs_reports_sprint_4_md_task_4_4, evals_config_support_copilot, docs_reports_sprint_4_md_nightly_yml_deviation [INFERRED 0.85]
- **Sprint 3 RAG pipeline stages: ingestion, collections, query/citations, web shell** — docs_reports_sprint_3_md_task_3_1, docs_reports_sprint_3_md_task_3_2, docs_reports_sprint_3_md_task_3_3, docs_reports_sprint_3_md_task_3_4 [EXTRACTED 1.00]
- **Gateway client call orchestration: routing -> transport -> ledger/cost -> budget** — apps_runtime_core_llm_client, apps_runtime_core_llm_routing, apps_runtime_core_llm_transport, apps_runtime_core_llm_ledger, fleet_api_budget [EXTRACTED 0.90]
- **KVKK Sensitivity Routing & Redaction Flow** — docs_source_technical_requirements_pii_pipeline, docs_source_technical_requirements_redaction_downgrade, docs_source_technical_requirements_sensitivity_routing, docs_source_technical_requirements_local_model_lane [EXTRACTED 0.90]
- **LLM Gateway Cost Governance (registry, budgets, spend ledger)** — docs_source_technical_requirements_llm_gateway, docs_source_technical_requirements_model_registry, docs_source_technical_requirements_budget_hierarchy, docs_source_technical_requirements_spend_ledger [EXTRACTED 0.85]
- **Guardrails + HITL External-Write Control** — docs_source_technical_requirements_guardrails_hitl, docs_source_technical_requirements_tool_risk_class, docs_source_technical_requirements_approval_queue, docs_source_technical_requirements_langgraph_runtime [EXTRACTED 0.85]
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

## Communities (184 total, 60 thin omitted)

### Community 0 - "RAG Query & Citations"
Cohesion: 0.06
Nodes (64): CitationOut, AsyncSession, BaseModel, query(), QueryIn, QueryOut, RAG query test harness (task 3.3): `/v1/rag/query`.  A chat-less endpoint that, Answer (+56 more)

### Community 1 - "Retention Purge Job"
Cohesion: 0.07
Nodes (51): apps/runtime/core/llm (gateway client), BudgetChecker, EmbeddingResponse, _first_content(), GatewayError, Ledger, LLMClient, LLMResponse (+43 more)

### Community 2 - "Document Upload & Chunking"
Cohesion: 0.05
Nodes (37): is_expired(), ObjectStore, purge_expired(), purge_expired_cron(), PurgeReport, Any, async_sessionmaker, datetime (+29 more)

### Community 3 - "Audit Logging"
Cohesion: 0.06
Nodes (37): ChatPage(), KnowledgePage(), metadata, AgentSummary, ChatMessage, ChatWindow(), FeedbackButtons(), FeedbackState (+29 more)

### Community 4 - "MinIO Object Store"
Cohesion: 0.08
Nodes (36): Chunk, chunk_text(), dedup_chunks(), Structure-aware chunking + content-hash dedup (TRD Sprint 3 task 3.1).  Splits, Pack paragraphs into chunks of at most `max_tokens` words each., Drop chunks whose content hash is already embedded (0 new-embedding re-upload)., _sha256(), EmbeddingClient (+28 more)

### Community 5 - "Web Shell Layout & Auth Routes"
Cohesion: 0.09
Nodes (40): Model, Model registry (TRD §4.1). Mirrored into the LiteLLM config., build_model_row(), evaluate_smoke(), _is_local(), ModelDraft, probe_model(), Connectivity/capability smoke probe for the model registry (task 2.2).  Runs a (+32 more)

### Community 6 - "Model Registry"
Cohesion: 0.08
Nodes (35): BudgetExceeded, BudgetStatus, check_budget(), DbBudgetChecker, evaluate_budget(), _period_start(), Any, async_sessionmaker (+27 more)

### Community 7 - "OCR Pipeline"
Cohesion: 0.08
Nodes (38): PROGRESS.md (Durable Status Log), Task 1.0 (git hook + convention) + 1.1 (monorepo + dev stack), Task 1.2 CI + migrations + seed, Task 1.3 auth core + 1.4 middleware + 1.5 Helm/k3d, Task 2.1 LiteLLM + 2.2 registry + 2.3 gateway client + 2.4 budgets, Task 3.1 ingestion pipeline + 3.2 collections/retention, Task 3.3 query + citations, Task 3.4 web shell + Knowledge UI (+30 more)

### Community 8 - "Collections API & Knowledge UI"
Cohesion: 0.09
Nodes (31): CurrentUser, _extract_roles(), _fetch_jwks(), get_current_user(), OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens., The authenticated principal extracted from a verified token., Verify a raw bearer token string and return the current user, or raise 401., Verify the bearer token and return the current user, or raise 401. (+23 more)

### Community 9 - "OIDC Token Verification"
Cohesion: 0.09
Nodes (30): AnalyzerEngine, _analyzer(), apply_pii_policy(), PiiFinding, PiiPolicyError, PolicyResult, Any, ValueError (+22 more)

### Community 10 - "PII Detection (Presidio)"
Cohesion: 0.09
Nodes (28): create_app(), FastAPI application factory., Build and configure the Fleet API application.      Set with_middleware=False, main(), Dump the FastAPI OpenAPI schema to a file for TS client generation., FastAPI, MonkeyPatch, TestClient (+20 more)

### Community 11 - "Gateway Client Factory"
Cohesion: 0.14
Nodes (33): Conversation, Feedback, Message, A chat thread with an agent (TRD §11)., A single turn in a conversation (TRD §11 — carries cost + citations)., Thumbs up/down on a message (TRD §11, §4.3 Chat UI AC)., User, AgentSummaryOut (+25 more)

### Community 12 - "Web TS Config"
Cohesion: 0.08
Nodes (25): annotate_roles(), build_client(), derive_role(), load_active_models(), Any, async_sessionmaker, Build a production LLMClient from settings + the model registry (task 2.3).  L, Map a default-matrix model name to its tier role for routing. (+17 more)

### Community 13 - "Gateway Client Embeddings"
Cohesion: 0.12
Nodes (15): CacheHit, _cosine(), Protocol, Redis-backed semantic cache (TRD §5).  Opt-in per agent (deterministic Q&A agent, RedisLike, SemanticCache, _FakeRedis, core.semantic_cache: Redis-backed semantic cache (task 4.2, TRD §5).  Opt-in per (+7 more)

### Community 14 - "LiteLLM Pricing Sync"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 15 - "Budget Enforcement"
Cohesion: 0.17
Nodes (26): CaseResult, EvalCase, evaluate_case(), _fold(), load_dataset(), main(), Eval runner (task 4.4, TRD §13.4): `make eval AGENT=x`.  Loads evals/datasets/<a, Returns (results, pass_rate, threshold). (+18 more)

### Community 16 - "Gateway Client Error Handling"
Cohesion: 0.13
Nodes (22): _clearance(), effective_sensitivity(), Any, Exception, Sensitivity routing — the KVKK guardrail (CLAUDE.md rule 2, TRD §4.3 + §8).  P, Ordered classification: public < internal < confidential < pii (§4.2)., Raised when no model's clearance covers the request's effective sensitivity., Return max(inputs), applying the §8 redaction-downgrade rule.      Content tha (+14 more)

### Community 17 - "Sensitivity Routing"
Cohesion: 0.13
Nodes (23): pricing_sync.py keeps prices in sync, _is_local(), _load_litellm_price_map(), main(), PriceValidationError, Any, Exception, Pricing sync for the LiteLLM proxy config (task 2.1).  Keeps the per-token inp (+15 more)

### Community 18 - "Text Extraction (PDF/DOCX)"
Cohesion: 0.17
Nodes (17): KillSwitch, Runtime-side enforcement, checked before any graph node runs a step., _Clock, _FakeRedis, datetime, core.killswitch: per-agent pause + global read-only mode (task 4.2, TRD §9).  Pe, redis-py returns bytes unless decode_responses=True was set on the     client —, test_agent_is_active_when_not_paused_in_redis() (+9 more)

### Community 19 - "FastAPI App Factory"
Cohesion: 0.15
Nodes (21): get_settings(), Application settings, loaded from the environment (pydantic-settings)., Return a fresh Settings instance (call at app creation, not import time)., Environment-driven configuration for the Fleet API., Settings, Document, Uploaded source document (TRD §11)., get_killswitch() (+13 more)

### Community 20 - "Department Agent Scenarios"
Cohesion: 0.23
Nodes (19): build_graph(), Compile the base graph for one agent, bound to a checkpointer for resume., _FakeLLMClient, _FakeRedis, _noop_tool(), Runtime base graph (task 4.1). AC: unit with FakeLLM — routing utility-vs- reaso, A write:internal tool with autonomy already granted reaches execute_tool     dir, Read-only can be flipped on by an admin while a HITL approval is     pending; th (+11 more)

### Community 21 - "Shared TS Client Deps"
Cohesion: 0.16
Nodes (16): ocr_image(), OcrResult, Any, Protocol, OCR step: vision-LLM primary, tesseract fallback (TRD §3 tech stack, task 3.1)., Run vision-LLM OCR; fall back to `tesseract_fn(image_bytes)` on failure/empty., _try_vision(), VisionClient (+8 more)

### Community 22 - "LLM Cost Computation"
Cohesion: 0.17
Nodes (18): _extension(), _extract_docx(), _extract_pdf(), extract_text(), _extract_txt(), ExtractResult, ValueError, Text extraction from uploaded documents (task 3.1: extract step).  Dispatches (+10 more)

### Community 23 - "Sprint 2 Plan (Source)"
Cohesion: 0.24
Nodes (19): Agent, Governed agent config (TRD §11, §4.2 tiering, §5 semantic cache, §9 kill switch), AgentIn, AgentOut, create_agent(), delete_agent(), get_agent(), list_agents() (+11 more)

### Community 24 - "TRD Core Concepts (Split)"
Cohesion: 0.18
Nodes (14): Citation, Generic citation carrier for the graph's citation-attach node (TRD §9, §11 messa, AgentSpec, GraphState, LangGraph base graph shared by every agent (task 4.1, killswitch 4.2).  Node ord, _tool_by_name(), ToolSpec, Integration: the runtime base graph against a REAL Postgres checkpointer (task 4 (+6 more)

### Community 25 - "API Settings"
Cohesion: 0.18
Nodes (14): _existing_hashes(), ingest_document(), Any, async_sessionmaker, QdrantClient, _QdrantSinkAdapter, arq worker: the `ingest_document` task and process entrypoint (task 3.1).  Wir, arq task: fetch the uploaded object, run the ingestion pipeline, persist chunks. (+6 more)

### Community 26 - "ORM Core Models"
Cohesion: 0.16
Nodes (17): Approval, AuditLog, Base, Budget, Chunk, Department, PromptVersion, SQLAlchemy declarative models for the first migration (users, departments, roles (+9 more)

### Community 27 - "Document ORM & Router"
Cohesion: 0.18
Nodes (18): Sprint 2 Report — LLM Gateway, Model Registry, Budgets, Security: API keys leaked into tracked .env.example, Dealer Onboarding — Corporate Sales, HR Talent & Onboarding — HR, budget.py — evaluate_budget + DbBudgetChecker, gateway/litellm/config.yaml, embeddings (text-embedding-3-small), Per-model fallback chains (+10 more)

### Community 28 - "Gateway Client Tests"
Cohesion: 0.19
Nodes (13): build_context(), Context, Any, Protocol, Conversation context budgeting: rolling window + summarized eviction (TRD §5)., The context to feed a call: an optional rolling summary plus recent turns., Split history into (summary of evicted turns, recent verbatim turns)., SummaryClient (+5 more)

### Community 29 - "Web Runtime Deps"
Cohesion: 0.13
Nodes (17): 15-Minute Demo Script, Sprint 0 — Prerequisites, Fleet Implementation Plan (Sprint Backlog), Dev Agent — IT / Engineering, Legal Document Review — Legal, Support Copilot — Customer Service, Wave Plan Overview, Deferrable Tasks (+9 more)

### Community 30 - "Web Dev Deps"
Cohesion: 0.12
Nodes (16): openapi-fetch, openapi-typescript, dependencies, openapi-fetch, devDependencies, openapi-typescript, typescript, typescript (+8 more)

### Community 31 - "Auth RBAC Integration Test"
Cohesion: 0.23
Nodes (14): collection_name(), delete_by_document(), ensure_collection(), Any, QdrantClient, qdrant_client_from_env(), Qdrant vector store (TRD §3 tech stack, tasks 3.1/3.3).  One Qdrant collection, Dense kNN search narrowed by an optional keyword (full-text) filter on     chun (+6 more)

### Community 32 - "Collection ORM & Router"
Cohesion: 0.21
Nodes (14): compute_cost(), parse_usage(), Any, Token-usage parsing and cost computation (TRD §5).  Pure helpers: read an Open, Token counts for one LLM call., Extract token counts from an OpenAI-style response body., Compute USD cost. Cached input tokens are billed at the cached price; the     r, Usage (+6 more)

### Community 33 - "Sprint 5 MCP Plan (Split)"
Cohesion: 0.15
Nodes (16): Sprint 2 — LLM Gateway, Model Registry, Budgets, Task 2.1 — LiteLLM proxy, Task 2.2 — Model registry, Task 2.3 — Gateway client (core/llm), Task 2.4 — Budgets, Budget Hierarchy, Sensitivity Clearance Rules, Cost & Token Optimization (+8 more)

### Community 34 - "Architecture Overview (Split)"
Cohesion: 0.12
Nodes (16): Rollout Modes (assist/supervised/autonomous), Generic Department Onboarding Checklist, PostgreSQL Data Model, TRD Design Principles, Environments, CI/CD, Backup, Langfuse LLM Observability, Observability (Logs/Traces/Metrics), Capability Phase Map (CORE/P2/P3) (+8 more)

### Community 35 - "Department Agent Registry"
Cohesion: 0.21
Nodes (14): _app_session_factory(), database_url(), get_engine(), get_session(), async_sessionmaker, AsyncSession, Async database engine, session factory, and URL resolution for the Fleet API., Return the async database URL from FLEET_DATABASE_URL, or the local default. (+6 more)

### Community 36 - "Budget Unit Tests"
Cohesion: 0.20
Nodes (13): detect_injection(), Untrusted-content quarantine + prompt-injection heuristics (CLAUDE.md rule 4, TR, Wrap retrieved/tool content in a quarantine block.      A single string is wrapp, Flag instruction-like patterns or encoded payloads in untrusted text., wrap_untrusted(), core.guardrails: untrusted-content quarantine + injection heuristics (task 4.1,, test_detect_injection_allows_ordinary_content(), test_detect_injection_flags_encoded_payload_marker() (+5 more)

### Community 37 - "CLAUDE.md Non-Negotiable Rules"
Cohesion: 0.18
Nodes (7): _default_now(), _is_flag_set(), _pause_key(), datetime, Protocol, Kill switches: per-agent pause + global read-only mode (TRD §9).  Per-agent `sta, RedisLike

### Community 38 - "Sensitivity Clearance Rules"
Cohesion: 0.21
Nodes (10): LangfuseScorer, Push a feedback score onto a Langfuse trace (TRD §6, task 4.3 AC: "👍/👎 lands in, score is +1 (thumbs up) or -1 (thumbs down); Langfuse NUMERIC score., AsyncBaseTransport, core.langfuse_client: push a feedback score onto a Langfuse trace (task 4.3, TRD, _RecordingTransport, test_push_score_body_carries_trace_id_and_value(), test_push_score_posts_to_scores_endpoint_with_basic_auth() (+2 more)

### Community 39 - "Model Gateway + Cost TRD (Split)"
Cohesion: 0.13
Nodes (15): dependencies, class-variance-authority, clsx, @fleet/shared, next-intl, @radix-ui/react-slot, tailwind-merge, tailwindcss (+7 more)

### Community 40 - "Project Overview: Platform"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, eslint-config-next, @eslint/eslintrc, @types/node, @types/react, @types/react-dom, typescript (+7 more)

### Community 41 - "Sprint 5/6 Plan + RAG Overview"
Cohesion: 0.17
Nodes (15): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.2 Ollama Host-Native with GPU, 0.4 Container-to-Host Ollama Reachability, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy, 2.2 Model Registry (+7 more)

### Community 42 - "Shared Package TS Config"
Cohesion: 0.36
Nodes (13): Collection, RAG document collection (TRD §8 data classification, §11)., CollectionIn, CollectionOut, create_collection(), delete_collection(), get_collection(), list_collections() (+5 more)

### Community 43 - "Observability Provisioning"
Cohesion: 0.18
Nodes (14): Sprint 3 — RAG, 3.1 Ingestion Pipeline, 3.2 Collections + Retention, 3.3 Query + Citations, 3.4 Web Shell + Knowledge UI, HITL Interrupt Node, Sprint 4 — Runtime, Chat, First Agent, 4.1 Runtime Core (+6 more)

### Community 44 - "Web Package Scripts"
Cohesion: 0.15
Nodes (14): Everything-is-an-API Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), n8n (queue mode), RAG Service, Redis, Redis 7 + arq Workers, FastAPI / Python 3.12 (+6 more)

### Community 45 - "Gateway Client Rule + Architecture"
Cohesion: 0.19
Nodes (12): Self-Service Analytics Agent (Data), Dealer Onboarding Agent (Corporate Sales), Dev Agent (IT/Engineering), HR Talent & Onboarding Agent(s) (HR), Insights Publisher Agent (Marketing), Invoice & Reconciliation Agent (Finance), Legal Document Review Agent (Legal), Listing Quality Agent (Listings Ops) (+4 more)

### Community 46 - "Sprint 4 Runtime Plan (Split)"
Cohesion: 0.18
Nodes (13): Rule 1: LLM calls only via gateway client, Rule 3: External side effects via MCP with risk_class, Non-Negotiable Rules, Rule 4: Retrieved/tool content is untrusted data, Dev Agent (IT / Engineering), Integration Layer (MCP), Approval Queue (LangGraph interrupt/resume), Guardrails & Human-in-the-Loop (§9) (+5 more)

### Community 47 - "Compose Infra (MinIO/Qdrant/Helm)"
Cohesion: 0.18
Nodes (13): Rule 2: Sensitivity routing enforced, Invoice & Reconciliation Agent (Finance), Talent & Onboarding Agent (HR), Vehicle Intake Agent (Trink sat!), Default Model Matrix (§4.2), Failure Behavior & Fallbacks (§4.4), Local-Model Lane (Ollama/vLLM, pii), Model Registry (§4.1) (+5 more)

### Community 48 - "Production Checklist & CI"
Cohesion: 0.18
Nodes (13): Sensitivity Clearance Ordering, Sensitivity Routing (KVKK), Budget Hierarchy, Spend Ledger, OWASP LLM Top 10 Mapping, Retention & Right to Erasure, Approval Queue (HITL), Tool Risk Class (+5 more)

### Community 49 - "Department Scenarios (Split)"
Cohesion: 0.21
Nodes (12): Agent Hub, Fleet AI Operations Platform, Integration Layer (MCP), Rollout Strategy Phases 0-3, Technology Coverage Map, Workflow Studio (n8n), Department Scenarios Wave Plan & Spec Template, Self-Service Analytics Agent (+4 more)

### Community 50 - "Sprint 3/6 Plan (Source)"
Cohesion: 0.20
Nodes (12): 10.1 Fresh-Install Rehearsal, docker-compose.dev.yml Stack, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack, 1.2 CI + Migrations + Seed, 1.3 Gateway Auth Core, 1.4 Gateway Cross-Cutting Middleware (+4 more)

### Community 51 - "Sprint 1 Plan (Source)"
Cohesion: 0.17
Nodes (11): compilerOptions, declaration, esModuleInterop, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

### Community 52 - "KVKK Local Lane Plan"
Cohesion: 0.27
Nodes (9): Tool risk_class -> approval-queue decision (TRD §9).  Pure decision logic, no I/, Return True if a tool call of this risk_class must go through HITL., requires_approval(), core.hitl: tool risk_class -> autonomous vs approval-queue decision (TRD §9).  P, test_read_tool_never_requires_approval(), test_write_external_always_requires_approval(), test_write_internal_autonomous_when_pass_rate_and_autonomy_both_clear(), test_write_internal_requires_approval_when_autonomy_disabled() (+1 more)

### Community 53 - "Sprint 1/10 Plan (Split)"
Cohesion: 0.22
Nodes (11): Commit & Branch Convention, Enable Branch Protection on main (pre-prod item), Production / Release Checklist, Sprint 1 Report — Repo, Stack, CI, Gateway, Environments, CI/CD, Backup (§14), Helm Umbrella Chart (one chart, k3d + prod), Keycloak OIDC AuthN, Observability (Langfuse, Prometheus, Grafana, Loki) (+3 more)

### Community 54 - "Sprint 2/6/7 Plan (Split)"
Cohesion: 0.18
Nodes (11): 15-Minute Demo Script, Sprint 10 — Demo Assembly & Docs, 10.2 Docs + Release, Sensitivity Routing Enforcement, No Cloud Egress Guarantee (pii lane), Sprint 8 — KVKK Lane, 8.1 Local-Lane Quality Rehearsal, 8.2 HR CV Mini-Flow (pii lane) (+3 more)

### Community 55 - "LiteLLM Config Tests"
Cohesion: 0.24
Nodes (11): 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue, 5.5 Dev Agent (Agent #3), write:external Approval Classification (+3 more)

### Community 56 - "Implementation Plan Method"
Cohesion: 0.22
Nodes (11): compose service: grafana, compose service: loki, compose service: prometheus, Grafana Loki Datasource, Grafana Prometheus Datasource, Grafana Service (Helm), Loki Service (Helm), Prometheus Service (Helm) (+3 more)

### Community 57 - "Demo Script & Sprint 9/10 Plan"
Cohesion: 0.24
Nodes (6): AsyncEngine, Append-only audit log writes., Insert one append-only audit row. Never updates or deletes., write_audit(), Request, Response

### Community 58 - "Sprint 0/2 Prerequisites"
Cohesion: 0.24
Nodes (8): AuditMiddleware, RateLimitMiddleware, Cross-cutting ASGI middleware: trace-id, append-only audit, and rate limiting., Assign a trace_id per request and echo it in the response header., Write an append-only audit row for each request, carrying the trace_id., Fixed-window per-client rate limiting backed by Redis., TraceIdMiddleware, BaseHTTPMiddleware

### Community 59 - "Sprint 1 Stage C Design Notes"
Cohesion: 0.27
Nodes (7): main(), Seed synthetic data and analytics fixture warehouse views. Idempotent., Support Copilot demo agent + its cs-help-center/cs-procedures collections     (, seed(), seed_support_copilot(), Integration test: seed inserts departments and creates the analytics fixture vie, test_seed_populates_and_creates_views()

### Community 60 - "GitHub Actions CI Jobs"
Cohesion: 0.29
Nodes (8): ensure_bucket(), minio_client_from_env(), Minio, MinIO object store for uploaded documents (TRD §3 tech stack, task 3.1).  Obje, _minio_up(), _qdrant_up(), Integration: MinIO + Qdrant stores against the real dev-stack containers (task, test_minio_bucket_roundtrip()

### Community 61 - "Gateway Client + Ledger"
Cohesion: 0.20
Nodes (9): name, private, scripts, build, dev, lint, start, typecheck (+1 more)

### Community 62 - "Guardrails & Approval Queue"
Cohesion: 0.20
Nodes (10): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, Deferrable Tasks List, 4.5 Agent Builder v1 [DEFERRABLE], Fleet AI Operations Platform, Problem Statement, Fleet Vision (single internal platform) (+2 more)

### Community 63 - "Analytics Agent + Migrations"
Cohesion: 0.20
Nodes (10): Agent Kill Switches, 4.2 Agent Registry + Semantic Cache + Kill Switches, Sprint 9 — Hardening, 9.1 Load Testing (k6), 9.3 Chaos-Lite + garak [DEFERRABLE], 9.4 Backup & Restore Drill, Agent Hub, Five Core Modules (+2 more)

### Community 64 - "Compose Core Services"
Cohesion: 0.29
Nodes (10): Sprint 6 — n8n Automations, 6.1 n8n Queue Mode + API Keys, 6.2 Automation #1 — Weekly Summary, 6.3 Automation #2 — Invoice Intake, Dealer Onboarding Agent (Corporate Sales), Department Use Cases, Insights Publisher (Marketing), Invoice & Reconciliation Agent (Finance) (+2 more)

### Community 65 - "Web/Auth Architecture (Split)"
Cohesion: 0.22
Nodes (10): compose service: minio, compose service: qdrant, Fleet Helm Umbrella Chart, MinIO Service (Helm), Helm Install NOTES, Qdrant Service (Helm), Fleet Dev (k3d) Values Overrides, MinIO Values (Helm defaults) (+2 more)

### Community 66 - "Privacy & KVKK Pipeline (Split)"
Cohesion: 0.36
Nodes (9): Knowledge Base (RAG), Sprint 8 — KVKK Lane, Support Copilot Agent, HR Talent & Onboarding Agent, Dealer Onboarding Agent, Legal Document Review Agent, Local-Model Lane (Ollama/vLLM), Privacy & KVKK (+1 more)

### Community 67 - "Sprint 1 Stage A + Keycloak Compose"
Cohesion: 0.25
Nodes (9): Invoice & Reconciliation — Finance, Vehicle Intake — Trink sat!, Sprint 3 — RAG, Sprint 6 — n8n Automations, Task 6.3 — Automation #2 invoice intake, Invoice & Reconciliation Agent, Vehicle Intake Agent, PII Pipeline (Presidio + TR recognizers) (+1 more)

### Community 68 - "Root Package Config"
Cohesion: 0.33
Nodes (9): Sprint 1 — Repo, Stack, CI, Gateway, Task 1.2 — CI + migrations + seed, Task 1.3 — Gateway auth core, Task 1.4 — Gateway cross-cutting middleware, Task 1.5 — Helm umbrella chart skeleton + k3d bootstrap, Sprint 1 Stage B Implementation Plan, Sprint 1 Stage C Implementation Plan, Sprint 1 Foundation Design Spec (+1 more)

### Community 69 - "CLAUDE.md Protocol Rules"
Cohesion: 0.25
Nodes (3): _names(), Static validation of the pinned LiteLLM config (task 2.1).  Guards the shape L, test_all_fallback_targets_are_defined_models()

### Community 70 - "K8s/Helm Foundations"
Cohesion: 0.43
Nodes (7): _collection_id(), main(), Any, async_sessionmaker, Seed the Support Copilot demo KB (task 4.4): upload evals/fixtures/support_copil, seed_docs(), _upsert_document()

### Community 71 - "Project Overview: Control Plane"
Cohesion: 0.32
Nodes (7): object_key(), sha256_bytes(), Object key + sha256 helpers for the MinIO document store (task 3.1).  The real, test_object_key_is_deterministic_and_namespaced_by_collection(), test_object_key_preserves_extension_case_insensitively(), test_sha256_bytes_differs_for_different_content(), test_sha256_bytes_is_stable()

### Community 72 - "Cost Optimization TRD (Source)"
Cohesion: 0.32
Nodes (7): attach_citations(), Any, Return a copy of response with a serialized citations list attached., core.citations: generic citation shape + attach helper (task 4.1).  Agent-specif, test_attach_citations_adds_list_to_response(), test_attach_citations_does_not_mutate_input_dict(), test_attach_citations_empty_list_yields_empty_key()

### Community 73 - "Sprint 3 RAG Plan (Split)"
Cohesion: 0.36
Nodes (8): Self-Service Analytics Agent (Text-to-SQL), Design Principles (gateway-everything, K8s-from-day-one), High-Level Architecture, LangGraph Agent Runtime (Postgres checkpointer), LLM Gateway (LiteLLM Proxy), Qdrant Vector DB, Technology Stack (Decided), Fleet Technical Requirements & System Design

### Community 74 - "Gateway Architecture (Split)"
Cohesion: 0.25
Nodes (8): FastAPI app factory (create_app), Keycloak aud claim mismatch risk, Cross-cutting middleware (trace_id, audit, rate-limit), OIDC token validation (Keycloak JWKS RS256), RBAC permission service (TRD 7.1 matrix), compose service: redis, Redis Service (Helm), Redis Values (Helm defaults)

### Community 75 - "Observability & Guardrails (Split)"
Cohesion: 0.39
Nodes (8): CI job: build-image (docker build + trivy scan), CI job: integration (pytest tests/integration, testcontainers), CI job: lint (ruff + mypy), CI job: security (bandit + gitleaks), CI job: unit (pytest tests/unit), CI GitHub Actions workflow, gitleaks/gitleaks-action@v2, Trivy scan via aquasec/trivy docker image (not trivy-action)

### Community 76 - "Local Model Lane (Split)"
Cohesion: 0.25
Nodes (7): @playwright/test, devDependencies, @playwright/test, name, private, scripts, test

### Community 77 - "Shared OpenAPI Schema"
Cohesion: 0.33
Nodes (6): point_id_for(), Deterministic point ID so re-embedding the same content upserts in place., Deterministic point-ID helper for the Qdrant store (task 3.1 dedup)., test_collection_name_namespaces_by_fleet_collection_id(), test_point_id_differs_for_different_hash(), test_point_id_is_deterministic_for_same_hash()

### Community 78 - "RAG Query Live Test"
Cohesion: 0.38
Nodes (7): Control Plane, Dev Agent, Approval Queue (interrupt/resume), RAG Grounding Check, Guardrails & Human-in-the-Loop, Kill Switches, Tool risk_class Classification

### Community 79 - "Web ESLint Config"
Cohesion: 0.29
Nodes (7): Self-Service Analytics — Data, Analytics fixture warehouse views, Task 5.2 — Analytics agent (agent #2), Alembic first migration (0001_initial), fleet_readonly read-only DB role, GitHub Actions CI pipeline (lint/unit/integration/security/build), Seed script with analytics fixture views (fixture_sales, fixture_orders)

### Community 80 - "Community 80"
Cohesion: 0.33
Nodes (7): Task 1.1 — Monorepo + dev stack, master_key gates admin/management API, compose service: langfuse, compose service: litellm, compose service: postgres, Postgres Service (Helm), Postgres Values (Helm defaults)

### Community 81 - "Community 81"
Cohesion: 0.29
Nodes (7): Keycloak (OIDC), Web UI (Next.js/TS), Next.js 15 Frontend, AuthN/AuthZ (Keycloak OIDC + RBAC), RBAC Role Matrix, End-User Screens, E2E Tests (Playwright)

### Community 82 - "Community 82"
Cohesion: 0.29
Nodes (7): Microsoft Presidio + TR Recognizers, Embedding Dedup (content_sha256), Loki Structured Logs, Data Classification (sensitivity levels), PII Pipeline (Presidio + TR recognizers), Redaction Downgrade Rule, chunks Table

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (7): Keycloak fleet realm with five test users, Sprint 1 Stage A Implementation Plan, pre-push git hook (task 1.0), Helm umbrella chart + k3d bootstrap, compose service: keycloak, Keycloak Service (Helm), Keycloak Values (Helm defaults)

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (6): name, packageManager, private, scripts, build, lint

### Community 85 - "Community 85"
Cohesion: 0.33
Nodes (3): _builder_token(), Integration: PII-sensitivity collection ingestion, end to end against the real, test_pii_collection_document_routes_to_local_embedding_lane()

### Community 87 - "Community 87"
Cohesion: 0.33
Nodes (5): configure_tracing(), new_trace_id(), OpenTelemetry setup (dev: logging exporter) and trace-id helpers., Install a console span exporter once (dev default per plan/TRD §14)., Generate a request trace id.

### Community 88 - "Community 88"
Cohesion: 0.33
Nodes (5): healthz(), Liveness and readiness endpoints., Liveness: the process is up., Readiness: the database is reachable., readyz()

### Community 89 - "Community 89"
Cohesion: 0.40
Nodes (6): Definition of Done, Doc/Split Sync Contract, Fleet Platform (CLAUDE.md guidance), Mandatory Skills (superpowers + graphify), PROGRESS.md Durable Memory Protocol, Task Execution Protocol

### Community 90 - "Community 90"
Cohesion: 0.33
Nodes (6): Dev setup bootstrap (task 10.1), Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four environments (local/test/demo-staging/prod), Shared Helm chart (per-env values), README.md — fleet-workflow

### Community 91 - "Community 91"
Cohesion: 0.33
Nodes (6): Agent Hub, Control Plane (guardrails, HITL, eval, audit), Fleet — AI Operations Platform (Overview), Knowledge Base (RAG), Support Copilot (Customer Service agent), Workflow Studio (n8n)

### Community 92 - "Community 92"
Cohesion: 0.47
Nodes (6): Budget Hierarchy (global→dept→agent→user), Cost & Token Optimization (§5), Data Model (PostgreSQL core tables, §11), Prompt Caching, Semantic Cache, Spend Ledger

### Community 93 - "Community 93"
Cohesion: 0.40
Nodes (6): Gateway-Everything Principle, LLM Gateway (LiteLLM Proxy), MCP Servers, Observability Stack (Langfuse/Prometheus/Grafana/Loki), Model Registry, Agent Builder Screen

### Community 94 - "Community 94"
Cohesion: 0.33
Nodes (6): Secure and Observable by Default, Langfuse (self-hosted), Trace ID Correlation, Langfuse LLM Layer (traces/generations), Output Guards (RAG grounding check), Evaluation (golden sets)

### Community 95 - "Community 95"
Cohesion: 0.47
Nodes (6): LiteLLM Proxy, Ollama (dev local models), vLLM (prod GPU), Fallback Chains & Circuit Breaking, Local-Model Lane (pii/confidential), Reference Sizing

### Community 96 - "Community 96"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 97 - "Community 97"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat SSE + feedback against the real dev stack (task 4.3 AC: "strea, test_chat_stream_renders_answer_and_feedback_lands_in_langfuse()

### Community 98 - "Community 98"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: document upload -> arq ingestion -> Qdrant, end to end against the, test_upload_document_ingests_and_lands_in_qdrant()

### Community 99 - "Community 99"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: `/v1/rag/query` end to end against the real dev-stack (task 3.3 AC, test_rag_query_returns_grounded_answer_with_citations()

### Community 100 - "Community 100"
Cohesion: 0.50
Nodes (3): Any, Protocol, ReasoningUtilityClient

### Community 101 - "Community 101"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 102 - "Community 102"
Cohesion: 0.40
Nodes (4): JWT, next-auth, next-auth/jwt, Session

### Community 103 - "Community 103"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 104 - "Community 104"
Cohesion: 0.40
Nodes (5): Security Testing (trivy/bandit/semgrep/ZAP/garak), Prometheus/Grafana Metrics, Prompt Injection Defense (quarantine blocks), Security Tests (garak/injection corpus), Risks & Mitigations

### Community 105 - "Community 105"
Cohesion: 0.40
Nodes (5): Default Model Matrix, Routing & Tiering (utility/reasoning), Model Tiering (utility vs reasoning), Prompt Caching, agents Table

### Community 106 - "Community 106"
Cohesion: 0.60
Nodes (4): Alembic environment. Uses a sync psycopg2 URL derived from FLEET_DATABASE_URL., run_migrations_offline(), run_migrations_online(), _sync_url()

### Community 107 - "Community 107"
Cohesion: 0.50
Nodes (3): _builder_token(), Integration: `/v1/admin/agents` CRUD + pause/resume against the real dev stack (, test_agent_crud_and_pause_blocks_a_real_graph_run()

### Community 112 - "Community 112"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 113 - "Community 113"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

### Community 121 - "Community 121"
Cohesion: 1.00
Nodes (3): openapi.json (dumped API schema), packages/shared README — @fleet/shared, src/schema.d.ts (generated, do not hand-edit)

## Ambiguous Edges - Review These
- `Self-Service Analytics Agent (Text-to-SQL)` → `Qdrant Vector DB`  [AMBIGUOUS]
  docs/source/PROJECT_OVERVIEW.md · relation: conceptually_related_to

## Knowledge Gaps
- **252 isolated node(s):** `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)`, `Listing Quality Agent (Listings Ops)`, `Insights Publisher Agent (Marketing)`, `Agent Hub` (+247 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **60 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Self-Service Analytics Agent (Text-to-SQL)` and `Qdrant Vector DB`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `LLMClient` connect `Retention Purge Job` to `API Settings`, `Gateway Client Factory`, `Web TS Config`, `Model Registry`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `gateway/litellm/config.yaml` connect `Document ORM & Router` to `Community 80`, `Retention Purge Job`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `KillSwitch` connect `Text Extraction (PDF/DOCX)` to `Community 100`, `CLAUDE.md Non-Negotiable Rules`, `Gateway Client Factory`, `FastAPI App Factory`, `Department Agent Scenarios`, `Community 86`, `Sprint 2 Plan (Source)`, `TRD Core Concepts (Split)`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `KillSwitch` (e.g. with `AgentIn` and `AgentOut`) actually correct?**
  _`KillSwitch` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `Hit` (e.g. with `AgentSummaryOut` and `ConversationIn`) actually correct?**
  _`Hit` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `AgentQueryConfig` (e.g. with `AgentSummaryOut` and `ConversationIn`) actually correct?**
  _`AgentQueryConfig` has 27 INFERRED edges - model-reasoned connections that need verification._
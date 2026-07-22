# Graph Report - .  (2026-07-22)

## Corpus Check
- 102 files · ~137,061 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2441 nodes · 4298 edges · 225 communities (162 shown, 63 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 930 edges (avg confidence: 0.7)
- Token cost: 100,000 input · 16,000 output

## Community Hubs (Navigation)
- RAG Query Endpoint
- Eval Runner
- API Data Models
- RAG Retention & Purge
- Dev Agent Graph
- MinIO Object Store
- RAG Chunking
- Postgres Read-Only Runner
- Docs & Department Scenarios
- API Database Layer
- Web App Shell & Layout
- RAG OCR Pipeline
- PII Detection & Redaction
- LLM Client Factory
- Semantic Cache
- MCP Base Server
- Web TypeScript Config
- LLM Client Unit Tests
- Analytics SQL Generator
- Runtime Base Graph
- LLM Sensitivity Routing
- API Auth (OIDC)
- Kill Switch
- Slack MCP Server
- LLM Gateway Client
- Jira MCP Server
- Model Registry
- Chat Router
- Dev Agent Run Endpoint
- Email MCP Server
- RAG Document Extraction
- Chat Analytics Reply Path
- Agents Admin Router
- LLM Budget Enforcement
- GitHub MCP Server
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
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
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
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
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
- Community 146
- Community 147
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 165
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 175
- Community 176
- Community 177
- Community 178
- Community 179
- Community 181
- Community 182
- Community 184
- Community 187
- Community 190
- Community 192
- Community 196
- Community 197
- Community 198
- Community 199
- Community 200
- Community 201
- Community 202
- Community 203
- Community 204
- Community 205
- Community 206
- Community 207
- Community 208
- Community 209
- Community 210
- Community 211
- Community 212
- Community 213
- Community 214
- Community 215
- Community 216
- Community 217
- Community 218
- Community 219
- Community 220
- Community 221
- Community 224

## God Nodes (most connected - your core abstractions)
1. `KillSwitch` - 51 edges
2. `GitHubTool` - 36 edges
3. `ToolContract` - 34 edges
4. `JiraTool` - 34 edges
5. `SlackPostTool` - 33 edges
6. `Hit` - 30 edges
7. `FakeTransport` - 26 edges
8. `LLMClient` - 23 edges
9. `FakeLedger` - 23 edges
10. `PgReadOnlyTool` - 23 edges

## Surprising Connections (you probably didn't know these)
- `test_smoke_on_add_marks_reachable_model_active()` --calls--> `ModelDraft`  [INFERRED]
  tests/integration/test_model_smoke_probe.py → apps/api/fleet_api/registry.py
- `test_smoke_on_add_marks_unknown_model_error()` --calls--> `ModelDraft`  [INFERRED]
  tests/integration/test_model_smoke_probe.py → apps/api/fleet_api/registry.py
- `Per-model fallback chains` --semantically_similar_to--> `Security: API keys leaked into tracked .env.example`  [INFERRED] [semantically similar]
  gateway/litellm/config.yaml → docs/reports/sprint-2.md
- `_client()` --calls--> `create_app()`  [INFERRED]
  tests/integration/test_auth_rbac.py → apps/api/fleet_api/app.py
- `test_healthz_ok()` --calls--> `create_app()`  [INFERRED]
  tests/unit/test_health.py → apps/api/fleet_api/app.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **HITL Interrupt/Resume/Approval Flow** — core_hitl_module, core_graph_module, approvals_router, dev_agent_graph [INFERRED 0.85]
- **Trace ID Forwarding Fix Across LLM Call Sites** — core_llm_client_module, fleet_rag_query_service_answer_query, core_langfuse_client_module, trace_id_forwarding_bug [INFERRED 0.85]
- **Support Copilot Demo Path (KB, agent, eval, e2e)** — support_copilot_agent, seed_docs_module, evals_runner_module, tests_e2e_chat_demo_path_spec, github_workflows_nightly [INFERRED 0.85]
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
- **KVKK Local Model Lane (no cloud egress for pii)** — docs_split_implementation_plan_sprint_8_kvkk_lane_no_cloud_egress_guarantee, docs_split_implementation_plan_sprint_2_llm_gateway_budgets_sensitivity_routing_enforcement, docs_split_implementation_plan_sprint_0_prerequisites_task_0_2_ollama_gpu, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.85]
- **Demo Script Agent Showcase** — docs_split_implementation_plan_sprint_4_runtime_chat_first_agent_task_4_4_support_copilot, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_task_5_5_dev_agent, docs_split_implementation_plan_sprint_6_n8n_automations_task_6_3_invoice_intake, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.90]
- **Cost Governance Stack** — docs_split_technical_requirements_05_cost_token_optimization_budget_hierarchy, docs_split_technical_requirements_05_cost_token_optimization_spend_ledger, docs_split_technical_requirements_05_cost_token_optimization_cost_anomaly_alerts, docs_split_technical_requirements_03_tech_stack_litellm [EXTRACTED 0.85]
- **Guardrails & HITL Approval Flow** — docs_split_technical_requirements_09_guardrails_hitl_tool_risk_class, docs_split_technical_requirements_09_guardrails_hitl_approval_queue, docs_split_technical_requirements_03_tech_stack_langgraph, docs_split_technical_requirements_11_data_model_core_tables [EXTRACTED 0.85]
- **Agents whose write:external actions are always approval-gated** — agent_dev_agent, agent_invoice_agent, agent_insights_publisher, agent_dealer_onboarding, concept_hitl_approval_queue, concept_risk_class [EXTRACTED 1.00]

## Communities (225 total, 63 thin omitted)

### Community 0 - "RAG Query Endpoint"
Cohesion: 0.06
Nodes (61): CitationOut, AsyncSession, BaseModel, query(), QueryIn, QueryOut, RAG query test harness (task 3.3): `/v1/rag/query`.  A chat-less endpoint that, Answer (+53 more)

### Community 1 - "Eval Runner"
Cohesion: 0.08
Nodes (66): AnalyticsAnswer, AnalyticsCase, CaseResult, DevAgentAnswer, DevAgentCase, EvalCase, evaluate_analytics_case(), evaluate_case() (+58 more)

### Community 2 - "API Data Models"
Cohesion: 0.06
Nodes (58): Agent, Approval, AuditLog, Base, Budget, Chunk, Collection, Conversation (+50 more)

### Community 3 - "RAG Retention & Purge"
Cohesion: 0.05
Nodes (37): is_expired(), ObjectStore, purge_expired(), purge_expired_cron(), PurgeReport, Any, async_sessionmaker, datetime (+29 more)

### Community 4 - "Dev Agent Graph"
Cohesion: 0.07
Nodes (50): build_dev_agent_graph(), DevAgentState, GitHubLike, JiraLike, Any, Protocol, ReasoningClient, TypedDict (+42 more)

### Community 5 - "MinIO Object Store"
Cohesion: 0.06
Nodes (41): ensure_bucket(), minio_client_from_env(), object_key(), Minio, MinIO object store for uploaded documents (TRD §3 tech stack, task 3.1).  Obje, sha256_bytes(), collection_name(), delete_by_document() (+33 more)

### Community 6 - "RAG Chunking"
Cohesion: 0.08
Nodes (36): Chunk, chunk_text(), dedup_chunks(), Structure-aware chunking + content-hash dedup (TRD Sprint 3 task 3.1).  Splits, Pack paragraphs into chunks of at most `max_tokens` words each., Drop chunks whose content hash is already embedded (0 new-embedding re-upload)., _sha256(), EmbeddingClient (+28 more)

### Community 7 - "Postgres Read-Only Runner"
Cohesion: 0.08
Nodes (34): AsyncpgRunner, build_default_runner(), Any, Real QueryRunner for pg_ro.PgReadOnlyTool, over the `fleet_readonly` role (task, _clamp_limit(), NonAllowlistedTableError, Any, Protocol (+26 more)

### Community 8 - "Docs & Department Scenarios"
Cohesion: 0.07
Nodes (41): Sprint 2 Report — LLM Gateway, Model Registry, Budgets, Security: API keys leaked into tracked .env.example, Dealer Onboarding — Corporate Sales, HR Talent & Onboarding — HR, budget.py — evaluate_budget + DbBudgetChecker, gateway/litellm/config.yaml, embeddings (text-embedding-3-small), Per-model fallback chains (+33 more)

### Community 9 - "API Database Layer"
Cohesion: 0.07
Nodes (37): _app_session_factory(), database_url(), get_engine(), get_session(), async_sessionmaker, AsyncSession, Async database engine, session factory, and URL resolution for the Fleet API., Return the async database URL from FLEET_DATABASE_URL, or the local default. (+29 more)

### Community 10 - "Web App Shell & Layout"
Cohesion: 0.09
Nodes (25): KnowledgePage(), metadata, DocumentStatusBadge(), VARIANT_BY_STATUS, Collection, Document, IN_FLIGHT_STATUSES, KnowledgeBrowser() (+17 more)

### Community 11 - "RAG OCR Pipeline"
Cohesion: 0.09
Nodes (30): ocr_image(), OcrResult, Any, Protocol, OCR step: vision-LLM primary, tesseract fallback (TRD §3 tech stack, task 3.1)., Run vision-LLM OCR; fall back to `tesseract_fn(image_bytes)` on failure/empty., _try_vision(), VisionClient (+22 more)

### Community 12 - "PII Detection & Redaction"
Cohesion: 0.09
Nodes (30): AnalyzerEngine, _analyzer(), apply_pii_policy(), PiiFinding, PiiPolicyError, PolicyResult, Any, ValueError (+22 more)

### Community 13 - "LLM Client Factory"
Cohesion: 0.08
Nodes (25): annotate_roles(), build_client(), derive_role(), load_active_models(), Any, async_sessionmaker, Build a production LLMClient from settings + the model registry (task 2.3).  L, Map a default-matrix model name to its tier role for routing. (+17 more)

### Community 14 - "Semantic Cache"
Cohesion: 0.12
Nodes (15): CacheHit, _cosine(), Protocol, Redis-backed semantic cache (TRD §5).  Opt-in per agent (deterministic Q&A age, RedisLike, SemanticCache, _FakeRedis, core.semantic_cache: Redis-backed semantic cache (task 4.2, TRD §5).  Opt-in p (+7 more)

### Community 15 - "MCP Base Server"
Cohesion: 0.11
Nodes (17): MCPAuthError, MCPServer, Any, Exception, Raised when a call_tool request carries a wrong/missing API key., Registry + dispatcher for one MCP server's tools., _validate_schema(), test_call_tool_unknown_tool_raises_key_error() (+9 more)

### Community 16 - "Web TypeScript Config"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 17 - "LLM Client Unit Tests"
Cohesion: 0.19
Nodes (22): _client(), FakeLedger, FakeTransport, Gateway client orchestration (task 2.3).  The client is the ONLY place LLM cal, §6 trace correlation: the proxy's Langfuse callback must tag the trace     with, Records calls; returns a canned OpenAI-style body, or raises to simulate     an, test_embeddings_forwards_trace_id_to_transport(), test_embeddings_pii_routes_to_local_model() (+14 more)

### Community 18 - "Analytics SQL Generator"
Cohesion: 0.14
Nodes (22): _build_system_prompt(), ClarificationNeeded, generate_sql(), Any, Exception, Protocol, NL question -> SQL (task 5.2, dept scenario 02 "SQL gen" call-site, TRD §4.3 rea, Some models wrap JSON in a ```json ... ``` fence despite being told not     to; (+14 more)

### Community 19 - "Runtime Base Graph"
Cohesion: 0.19
Nodes (20): build_graph(), Compile the base graph for one agent, bound to a checkpointer for resume., _FakeLLMClient, _FakeRedis, _noop_tool(), Any, Runtime base graph (task 4.1). AC: unit with FakeLLM — routing utility-vs- reas, A write:internal tool with autonomy already granted reaches execute_tool     di (+12 more)

### Community 20 - "LLM Sensitivity Routing"
Cohesion: 0.13
Nodes (22): _clearance(), effective_sensitivity(), Any, Exception, Sensitivity routing — the KVKK guardrail (CLAUDE.md rule 2, TRD §4.3 + §8).  P, Ordered classification: public < internal < confidential < pii (§4.2)., Raised when no model's clearance covers the request's effective sensitivity., Return max(inputs), applying the §8 redaction-downgrade rule.      Content tha (+14 more)

### Community 21 - "API Auth (OIDC)"
Cohesion: 0.13
Nodes (22): CurrentUser, _extract_roles(), _fetch_jwks(), get_current_user(), OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens., The authenticated principal extracted from a verified token., Verify a raw bearer token string and return the current user, or raise 401., Verify the bearer token and return the current user, or raise 401. (+14 more)

### Community 22 - "Kill Switch"
Cohesion: 0.17
Nodes (17): KillSwitch, Runtime-side enforcement, checked before any graph node runs a step., _Clock, _FakeRedis, datetime, core.killswitch: per-agent pause + global read-only mode (task 4.2, TRD §9)., redis-py returns bytes unless decode_responses=True was set on the     client —, test_agent_is_active_when_not_paused_in_redis() (+9 more)

### Community 23 - "Slack MCP Server"
Cohesion: 0.14
Nodes (15): build_default_sender(), DisallowedChannelError, Exception, Protocol, slack MCP tool: slack.post via incoming webhook (task 5.3, dept scenario 03).  w, Target channel is outside the server's allowlist., Real transport: one incoming-webhook URL per Fleet deployment. Slack     incomin, SlackPostTool (+7 more)

### Community 24 - "LLM Gateway Client"
Cohesion: 0.17
Nodes (13): _first_content(), GatewayError, LLMResponse, _opt_float(), Any, Exception, Planning / generation / judgment call-sites (§4.3)., Classification / extraction / routing / summarization call-sites (§4.3). (+5 more)

### Community 25 - "Jira MCP Server"
Cohesion: 0.13
Nodes (13): build_default_backend(), FixtureJiraBackend, IssueNotFoundError, JiraBackend, Any, Exception, Protocol, jira MCP tool: search/get_issue (task 5.3, dept scenario 03 Dev Agent).  # INTEG (+5 more)

### Community 26 - "Model Registry"
Cohesion: 0.20
Nodes (19): build_model_row(), evaluate_smoke(), _is_local(), ModelDraft, Any, Model registry domain logic (task 2.2).  Pure, transport-free helpers for the, An admin-submitted model definition (Admin → Models add form, §4.1)., Outcome of the connectivity/capability probe run on add. (+11 more)

### Community 27 - "Chat Router"
Cohesion: 0.20
Nodes (20): AgentSummaryOut, ConversationIn, ConversationOut, FeedbackIn, get_killswitch(), get_langfuse_scorer(), list_chat_agents(), MessageIn (+12 more)

### Community 28 - "Dev Agent Run Endpoint"
Cohesion: 0.14
Nodes (16): AsyncSession, BaseModel, Dev Agent run trigger (task 5.5, dept scenario 03).  `POST /v1/dev-agent/runs` s, RunIn, RunOut, start_run(), BranchNamePatternError, GitHubTool (+8 more)

### Community 29 - "Email MCP Server"
Cohesion: 0.17
Nodes (13): EmailSender, EmailSendTool, InvalidRecipientError, Exception, Protocol, email MCP tool: SMTP sandbox send (task 5.1).  Always write:external (TRD §9 nam, Recipient address is malformed or outside the allowed domain set., _FakeSender (+5 more)

### Community 30 - "RAG Document Extraction"
Cohesion: 0.17
Nodes (18): _extension(), _extract_docx(), _extract_pdf(), extract_text(), _extract_txt(), ExtractResult, ValueError, Text extraction from uploaded documents (task 3.1: extract step).  Dispatches (+10 more)

### Community 31 - "Chat Analytics Reply Path"
Cohesion: 0.17
Nodes (20): Agent, _analytics_reply(), _assert_agent_may_read_its_collections(), create_conversation(), _get_or_create_user(), Any, AsyncSession, CurrentUser (+12 more)

### Community 32 - "Agents Admin Router"
Cohesion: 0.19
Nodes (19): AgentIn, AgentOut, create_agent(), delete_agent(), get_agent(), get_killswitch(), list_agents(), pause_agent() (+11 more)

### Community 33 - "LLM Budget Enforcement"
Cohesion: 0.16
Nodes (15): BudgetExceeded, BudgetStatus, check_budget(), DbBudgetChecker, _period_start(), Any, async_sessionmaker, datetime (+7 more)

### Community 34 - "GitHub MCP Server"
Cohesion: 0.18
Nodes (7): build_default_backend(), GitHubBackend, Any, Protocol, github MCP tool: read_repo/create_branch/open_pr (task 5.3, dept scenario 03 Dev, RestGitHubBackend, AsyncClient

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (14): apps/runtime/core/llm (gateway client), BudgetChecker, EmbeddingResponse, Ledger, Protocol, LLM gateway client — the only place provider LLM calls are made (CLAUDE.md rule, Sends a chat completion to the proxy and returns the raw response body., Persists a spend_ledger row. (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.18
Nodes (13): build_context(), Context, Any, Protocol, Conversation context budgeting: rolling window + summarized eviction (TRD §5)., The context to feed a call: an optional rolling summary plus recent turns., Split history into (summary of evicted turns, recent verbatim turns)., SummaryClient (+5 more)

### Community 37 - "Community 37"
Cohesion: 0.13
Nodes (17): 15-Minute Demo Script, Sprint 0 — Prerequisites, Fleet Implementation Plan (Sprint Backlog), Dev Agent — IT / Engineering, Legal Document Review — Legal, Support Copilot — Customer Service, Wave Plan Overview, Deferrable Tasks (+9 more)

### Community 38 - "Community 38"
Cohesion: 0.12
Nodes (16): openapi-fetch, openapi-typescript, dependencies, openapi-fetch, devDependencies, openapi-typescript, typescript, typescript (+8 more)

### Community 39 - "Community 39"
Cohesion: 0.27
Nodes (13): _FakeLLM, _FakeSlackSender, _labeled_ticket(), agents.dev_agent.graph: ticket -> plan -> branch -> PR -> Slack, with a single H, Caught before shipping: a raised slack.post() (e.g. an unset/invalid     webhook, test_approve_resumes_and_opens_pr_and_notifies_slack(), test_oversized_diff_never_creates_branch(), test_plan_touching_protected_path_never_creates_branch() (+5 more)

### Community 40 - "Community 40"
Cohesion: 0.28
Nodes (14): Model, Model registry (TRD §4.1). Mirrored into the LiteLLM config., add_model(), delete_model(), get_model(), list_models(), ModelIn, ModelOut (+6 more)

### Community 41 - "Community 41"
Cohesion: 0.32
Nodes (14): MCPValidationError, MCP server base: tool registry with declared risk_class, schema validation, and, Raised when a call_tool payload fails the tool's input_schema., ToolContract, _echo(), _make_server(), fleet_mcp.base: MCP server base — tool registry, risk_class, schema validation,, test_call_tool_missing_required_field_raises_validation_error() (+6 more)

### Community 42 - "Community 42"
Cohesion: 0.21
Nodes (14): compute_cost(), parse_usage(), Any, Token-usage parsing and cost computation (TRD §5).  Pure helpers: read an Open, Token counts for one LLM call., Extract token counts from an OpenAI-style response body., Compute USD cost. Cached input tokens are billed at the cached price; the     r, Usage (+6 more)

### Community 43 - "Community 43"
Cohesion: 0.15
Nodes (16): Sprint 2 — LLM Gateway, Model Registry, Budgets, Task 2.1 — LiteLLM proxy, Task 2.2 — Model registry, Task 2.3 — Gateway client (core/llm), Task 2.4 — Budgets, Budget Hierarchy, Sensitivity Clearance Rules, Cost & Token Optimization (+8 more)

### Community 44 - "Community 44"
Cohesion: 0.12
Nodes (16): Rollout Modes (assist/supervised/autonomous), Generic Department Onboarding Checklist, PostgreSQL Data Model, TRD Design Principles, Environments, CI/CD, Backup, Langfuse LLM Observability, Observability (Logs/Traces/Metrics), Capability Phase Map (CORE/P2/P3) (+8 more)

### Community 45 - "Community 45"
Cohesion: 0.24
Nodes (10): _FakeBackend, fleet_mcp.servers.github: read_repo/create_branch/open_pr (task 5.3, dept scenar, test_commit_file_with_agent_prefix_succeeds(), test_commit_file_without_agent_prefix_is_rejected(), test_contracts_declare_correct_risk_classes(), test_create_branch_with_agent_prefix_succeeds(), test_create_branch_without_agent_prefix_is_rejected(), test_open_pr_always_dispatches_regardless_of_content() (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (11): create_app(), FastAPI application factory., Build and configure the Fleet API application.      Set with_middleware=False, main(), Dump the FastAPI OpenAPI schema to a file for TS client generation., FastAPI, Integration test: an audit row is written with the request trace_id, and the ra, test_audit_row_has_trace_id() (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.19
Nodes (10): InternalMockTool, Any, Exception, internal-mock MCP tool: fixture-backed stand-in for an internal API (task 5.1)., No fixture record exists for the given id., RecordNotFoundError, fleet_mcp.servers.internal_mock: fixture-backed internal API mock (task 5.1).  #, test_contract_declares_read_risk_class() (+2 more)

### Community 48 - "Community 48"
Cohesion: 0.21
Nodes (10): AgentSpec, LangGraph base graph shared by every agent (task 4.1, killswitch 4.2).  Node o, _tool_by_name(), ToolSpec, Integration: the runtime base graph against a REAL Postgres checkpointer (task, Always proposes the same write:external tool call, regardless of tier., _Resp, _send_email() (+2 more)

### Community 49 - "Community 49"
Cohesion: 0.20
Nodes (13): detect_injection(), Untrusted-content quarantine + prompt-injection heuristics (CLAUDE.md rule 4, TR, Wrap retrieved/tool content in a quarantine block.      A single string is wra, Flag instruction-like patterns or encoded payloads in untrusted text., wrap_untrusted(), core.guardrails: untrusted-content quarantine + injection heuristics (task 4.1,, test_detect_injection_allows_ordinary_content(), test_detect_injection_flags_encoded_payload_marker() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.18
Nodes (7): _default_now(), _is_flag_set(), _pause_key(), datetime, Protocol, Kill switches: per-agent pause + global read-only mode (TRD §9).  Per-agent `s, RedisLike

### Community 51 - "Community 51"
Cohesion: 0.21
Nodes (10): LangfuseScorer, Push a feedback score onto a Langfuse trace (TRD §6, task 4.3 AC: "👍/👎 lands in, score is +1 (thumbs up) or -1 (thumbs down); Langfuse NUMERIC score., AsyncBaseTransport, core.langfuse_client: push a feedback score onto a Langfuse trace (task 4.3, TRD, _RecordingTransport, test_push_score_body_carries_trace_id_and_value(), test_push_score_posts_to_scores_endpoint_with_basic_auth() (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.29
Nodes (10): LLMClient, Governed entry point for LLM calls. Construct once per process with the     mod, _checker(), FakeLedger, FakeTransport, Budget enforcement inside the gateway client (task 2.4).  The client runs a bu, test_hard_stop_blocks_call_and_bills_nothing(), test_no_checker_means_no_enforcement() (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (15): dependencies, class-variance-authority, clsx, @fleet/shared, next-intl, @radix-ui/react-slot, tailwind-merge, tailwindcss (+7 more)

### Community 54 - "Community 54"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, eslint-config-next, @eslint/eslintrc, @types/node, @types/react, @types/react-dom, typescript (+7 more)

### Community 55 - "Community 55"
Cohesion: 0.25
Nodes (14): MonkeyPatch, _admin_token(), backing_stack(), _client(), keycloak(), _provision_realm(), Integration test: 401 without/with a bad token, 200 with a valid member token,, Real Postgres + Redis so the audit/rate-limit middleware runs for real     inst (+6 more)

### Community 56 - "Community 56"
Cohesion: 0.21
Nodes (11): AnalyticsResult, ask_analytics(), GovernedQueryTool, Any, Protocol, ReasoningClient, Analytics agent orchestration: NL question -> SQL -> governed execution (task 5., GovernedToolRefusal (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.19
Nodes (14): 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue, 5.5 Dev Agent (Agent #3), write:external Approval Classification (+6 more)

### Community 58 - "Community 58"
Cohesion: 0.15
Nodes (14): Everything-is-an-API Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), n8n (queue mode), RAG Service, Redis, Redis 7 + arq Workers, FastAPI / Python 3.12 (+6 more)

### Community 59 - "Community 59"
Cohesion: 0.26
Nodes (10): _FakeLLM, _FakeRunner, _pg_tool(), agents.analytics.service: orchestrates NL question -> SQL -> governed execution, Caught live (test_chat_analytics_live.py): chat.py passes     sensitivity=agent., test_ambiguous_question_raises_clarification(), test_clear_question_returns_sql_and_rows(), test_generated_sql_is_always_surfaced_alongside_rows() (+2 more)

### Community 60 - "Community 60"
Cohesion: 0.19
Nodes (12): Self-Service Analytics Agent (Data), Dealer Onboarding Agent (Corporate Sales), Dev Agent (IT/Engineering), HR Talent & Onboarding Agent(s) (HR), Insights Publisher Agent (Marketing), Invoice & Reconciliation Agent (Finance), Legal Document Review Agent (Legal), Listing Quality Agent (Listings Ops) (+4 more)

### Community 61 - "Community 61"
Cohesion: 0.19
Nodes (13): Analytics Agent (#2), Approval Queue (HITL), apps/api/fleet_api/routers/approvals.py, Rationale: deterministic branch_suffix collision on repeated runs, Dev Agent (#3), agents/dev_agent/graph.py (dedicated LangGraph), Sprint 5 Report — MCP, Agents #2-3, Approvals, apps/mcp/fleet_mcp/base.py (MCPServer, ToolContract) (+5 more)

### Community 62 - "Community 62"
Cohesion: 0.31
Nodes (8): JiraTool, _backend(), _FixtureBackend, fleet_mcp.servers.jira: fixture-backed Jira mock + real-config option (task 5.3,, test_contracts_declare_read_risk_class(), test_get_issue_raises_on_unknown_key(), test_get_issue_returns_issue_by_key(), test_search_returns_matching_issues()

### Community 63 - "Community 63"
Cohesion: 0.23
Nodes (11): attach_citations(), Citation, Any, Generic citation carrier for the graph's citation-attach node (TRD §9, §11 messa, Return a copy of response with a serialized citations list attached., GraphState, TypedDict, core.citations: generic citation shape + attach helper (task 4.1).  Agent-spec (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.26
Nodes (12): evaluate_budget(), Decide allow/soft/hard for `spent_usd` against `limit_usd`.      No limit (``N, Budget decision logic (task 2.4, TRD §5).  Pure evaluation of spend against a, test_at_hard_limit_is_blocked(), test_at_soft_limit_sets_soft_flag_but_still_allowed(), test_between_soft_and_hard_is_allowed_and_flagged(), test_no_budget_row_is_unlimited(), test_over_hard_limit_is_blocked() (+4 more)

### Community 65 - "Community 65"
Cohesion: 0.21
Nodes (8): AgentSummary, ChatMessage, ChatWindow(), FeedbackButtons(), FeedbackState, ChatStreamEvent, parseSseBlock(), streamChatMessage()

### Community 66 - "Community 66"
Cohesion: 0.18
Nodes (13): Rule 3: External side effects via MCP with risk_class, Non-Negotiable Rules, Rule 4: Retrieved/tool content is untrusted data, Dev Agent (IT / Engineering), Integration Layer (MCP), Approval Queue (LangGraph interrupt/resume), Guardrails & Human-in-the-Loop (§9), LLM-Specific Security (OWASP LLM Top 10, §7.3) (+5 more)

### Community 67 - "Community 67"
Cohesion: 0.18
Nodes (13): Rule 2: Sensitivity routing enforced, Invoice & Reconciliation Agent (Finance), Talent & Onboarding Agent (HR), Vehicle Intake Agent (Trink sat!), Default Model Matrix (§4.2), Failure Behavior & Fallbacks (§4.4), Local-Model Lane (Ollama/vLLM, pii), Model Registry (§4.1) (+5 more)

### Community 68 - "Community 68"
Cohesion: 0.18
Nodes (13): Sensitivity Clearance Ordering, Sensitivity Routing (KVKK), Budget Hierarchy, Spend Ledger, OWASP LLM Top 10 Mapping, Retention & Right to Erasure, Approval Queue (HITL), Tool Risk Class (+5 more)

### Community 69 - "Community 69"
Cohesion: 0.23
Nodes (9): build_ocr_contract(), build_ocr_tool(), Any, ocr MCP tool: wraps fleet_rag.ingest.ocr for tool-calling agents (task 5.1).  Th, fleet_mcp.servers.ocr: MCP wrapper around fleet_rag.ingest.ocr (task 5.1).  Thin, _StubVisionClient, test_ocr_tool_extracts_text_from_base64_image(), test_ocr_tool_falls_back_to_tesseract_on_vision_failure() (+1 more)

### Community 70 - "Community 70"
Cohesion: 0.21
Nodes (12): Agent Hub, Fleet AI Operations Platform, Integration Layer (MCP), Rollout Strategy Phases 0-3, Technology Coverage Map, Workflow Studio (n8n), Department Scenarios Wave Plan & Spec Template, Self-Service Analytics Agent (+4 more)

### Community 71 - "Community 71"
Cohesion: 0.23
Nodes (12): 5.2 Analytics Agent (Agent #2), 6.3 Automation #2 — Invoice Intake, Knowledge Base (RAG), Dealer Onboarding Agent (Corporate Sales), Department Use Cases, Document Review Assistant (Legal & Compliance), Invoice & Reconciliation Agent (Finance), Listing Quality Agent (+4 more)

### Community 72 - "Community 72"
Cohesion: 0.17
Nodes (11): compilerOptions, declaration, esModuleInterop, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

### Community 73 - "Community 73"
Cohesion: 0.24
Nodes (3): _FakeGitHubBackend, _FakeJiraBackend, Any

### Community 74 - "Community 74"
Cohesion: 0.29
Nodes (10): ApprovalOut, decide_approval(), DecisionIn, list_approvals(), AsyncSession, BaseModel, CurrentUser, Approval queue: list pending items, approve/edit/reject with LangGraph resume (t (+2 more)

### Community 75 - "Community 75"
Cohesion: 0.24
Nodes (6): Analytics agent's semantic layer: view/column glossary the SQL generator grounds, SemanticLayer, ViewSpec, agents.analytics.semantic_layer: view/column glossary the SQL generator grounds, test_allowlisted_tables_match_view_names(), test_describe_renders_view_and_column_glossary()

### Community 76 - "Community 76"
Cohesion: 0.27
Nodes (9): Tool risk_class -> approval-queue decision (TRD §9).  Pure decision logic, no, Return True if a tool call of this risk_class must go through HITL., requires_approval(), core.hitl: tool risk_class -> autonomous vs approval-queue decision (TRD §9)., test_read_tool_never_requires_approval(), test_write_external_always_requires_approval(), test_write_internal_autonomous_when_pass_rate_and_autonomy_both_clear(), test_write_internal_requires_approval_when_autonomy_disabled() (+1 more)

### Community 77 - "Community 77"
Cohesion: 0.24
Nodes (11): Task 4.4 Support Copilot agent + evals + Playwright E2E, Task 5.2 Analytics agent, TRD §13.4 Per-agent eval threshold policy, evals/config.yaml (per-agent thresholds), evals/runner.py, Nightly GitHub Actions Workflow, Nightly e2e Job, Nightly eval Job (+3 more)

### Community 78 - "Community 78"
Cohesion: 0.22
Nodes (11): compose service: grafana, compose service: loki, compose service: prometheus, Grafana Loki Datasource, Grafana Prometheus Datasource, Grafana Service (Helm), Loki Service (Helm), Prometheus Service (Helm) (+3 more)

### Community 79 - "Community 79"
Cohesion: 0.27
Nodes (8): AppError, ForbiddenError, install_error_handlers(), FastAPI, Domain error model and FastAPI exception handlers., Base class for domain errors mapped to HTTP responses., Register a handler that renders AppError as a structured JSON body., Exception

### Community 80 - "Community 80"
Cohesion: 0.24
Nodes (8): AuditMiddleware, RateLimitMiddleware, Cross-cutting ASGI middleware: trace-id, append-only audit, and rate limiting., Assign a trace_id per request and echo it in the response header., Write an append-only audit row for each request, carrying the trace_id., Fixed-window per-client rate limiting backed by Redis., TraceIdMiddleware, BaseHTTPMiddleware

### Community 81 - "Community 81"
Cohesion: 0.22
Nodes (7): probe_model(), Connectivity/capability smoke probe for the model registry (task 2.2).  Runs a, Send a 1-token completion to `draft.litellm_model_id` via the proxy.      Reac, fleet_api/registry.py — model registry, Integration: the model registry smoke-test-on-add path against the LIVE LiteLLM, test_smoke_on_add_marks_reachable_model_active(), test_smoke_on_add_marks_unknown_model_error()

### Community 82 - "Community 82"
Cohesion: 0.20
Nodes (9): name, private, scripts, build, dev, lint, start, typecheck (+1 more)

### Community 83 - "Community 83"
Cohesion: 0.27
Nodes (10): Rule 1: LLM calls only via gateway client, Self-Service Analytics Agent (Text-to-SQL), Design Principles (gateway-everything, K8s-from-day-one), High-Level Architecture, Keycloak OIDC AuthN, LangGraph Agent Runtime (Postgres checkpointer), LLM Gateway (LiteLLM Proxy), Qdrant Vector DB (+2 more)

### Community 84 - "Community 84"
Cohesion: 0.22
Nodes (10): Deferrable Tasks List, HITL Interrupt Node, Agent Kill Switches, Sprint 4 — Runtime, Chat, First Agent, 4.1 Runtime Core, 4.2 Agent Registry + Semantic Cache + Kill Switches, 4.5 Agent Builder v1 [DEFERRABLE], 7.3 Admin System-Health Screen [DEFERRABLE] (+2 more)

### Community 85 - "Community 85"
Cohesion: 0.22
Nodes (10): compose service: minio, compose service: qdrant, Fleet Helm Umbrella Chart, MinIO Service (Helm), Helm Install NOTES, Qdrant Service (Helm), Fleet Dev (k3d) Values Overrides, MinIO Values (Helm defaults) (+2 more)

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (7): _load_dotenv_fallback(), Integration: full Dev Agent chain against the real dev stack + sandbox GitHub re, _set_common_env(), test_approve_path_opens_real_pr_on_sandbox(), test_reject_path_never_opens_a_pr(), test_unlabeled_ticket_is_blocked_before_any_branch_creation(), _token()

### Community 87 - "Community 87"
Cohesion: 0.25
Nodes (5): build_default_sender(), Real SMTP transport for email.EmailSendTool (task 5.1).  Talks to the sandbox SM, SmtpSender, Integration: email MCP tool against the real mailpit SMTP sandbox (task 5.1 AC —, test_live_send_lands_in_mailpit()

### Community 88 - "Community 88"
Cohesion: 0.25
Nodes (9): Commit & Branch Convention, Enable Branch Protection on main (pre-prod item), Production / Release Checklist, Sprint 1 Report — Repo, Stack, CI, Gateway, Environments, CI/CD, Backup (§14), Helm Umbrella Chart (one chart, k3d + prod), Observability (Langfuse, Prometheus, Grafana, Loki), Testing Strategy (§13) (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.36
Nodes (9): Knowledge Base (RAG), Sprint 8 — KVKK Lane, Support Copilot Agent, HR Talent & Onboarding Agent, Dealer Onboarding Agent, Legal Document Review Agent, Local-Model Lane (Ollama/vLLM), Privacy & KVKK (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.25
Nodes (9): Invoice & Reconciliation — Finance, Vehicle Intake — Trink sat!, Sprint 3 — RAG, Sprint 6 — n8n Automations, Task 6.3 — Automation #2 invoice intake, Invoice & Reconciliation Agent, Vehicle Intake Agent, PII Pipeline (Presidio + TR recognizers) (+1 more)

### Community 91 - "Community 91"
Cohesion: 0.33
Nodes (9): Sprint 1 — Repo, Stack, CI, Gateway, Task 1.2 — CI + migrations + seed, Task 1.3 — Gateway auth core, Task 1.4 — Gateway cross-cutting middleware, Task 1.5 — Helm umbrella chart skeleton + k3d bootstrap, Sprint 1 Stage B Implementation Plan, Sprint 1 Stage C Implementation Plan, Sprint 1 Foundation Design Spec (+1 more)

### Community 92 - "Community 92"
Cohesion: 0.25
Nodes (9): 0.2 Ollama Host-Native with GPU, Sensitivity Routing Enforcement, No Cloud Egress Guarantee (pii lane), Sprint 8 — KVKK Lane, 8.1 Local-Lane Quality Rehearsal, 8.2 HR CV Mini-Flow (pii lane), 8.3 Erasure + Clearance Surfacing, 8.4 PII Masking Verification (+1 more)

### Community 93 - "Community 93"
Cohesion: 0.28
Nodes (9): 10.1 Fresh-Install Rehearsal, docker-compose.dev.yml Stack, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack, 1.2 CI + Migrations + Seed, 1.3 Gateway Auth Core, 1.4 Gateway Cross-Cutting Middleware (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.25
Nodes (9): 2.2 Model Registry, Sprint 6 — n8n Automations, 6.1 n8n Queue Mode + API Keys, 6.2 Automation #1 — Weekly Summary, Sprint 7 — Admin & Observability, 7.1 Admin: Users, Models, Budgets, API Keys, 7.2 Cost Dashboard, Approvals, Audit Explorer, 7.4 Grafana + Alerting as Code (+1 more)

### Community 95 - "Community 95"
Cohesion: 0.22
Nodes (7): @playwright/test, devDependencies, @playwright/test, name, private, scripts, test

### Community 96 - "Community 96"
Cohesion: 0.25
Nodes (3): _names(), Static validation of the pinned LiteLLM config (task 2.1).  Guards the shape L, test_all_fallback_targets_are_defined_models()

### Community 97 - "Community 97"
Cohesion: 0.39
Nodes (8): apps/runtime/agents/analytics package, agents/analytics/service.py (ask_analytics), agents/analytics/sql_generator.py (generate_sql), core/errors.py (GovernedToolRefusal), Task 5.1 MCP base + first servers, apps/mcp/fleet_mcp/servers/pg_ro.py (PgReadOnlyTool), Migration 0007: GRANT fleet_readonly TO CURRENT_USER, Rationale: SQL generator markdown code-fence wrapping JSON

### Community 98 - "Community 98"
Cohesion: 0.32
Nodes (7): Permission, permissions_for(), Role-based access control: roles, permissions, and the enforcement dependency., Union of permissions granted by the user's roles., Dependency factory: allow the request only if the user holds `perm`., require_permission(), StrEnum

### Community 99 - "Community 99"
Cohesion: 0.36
Nodes (8): core/killswitch.py (KillSwitch), core/semantic_cache.py (SemanticCache), PROGRESS.md (durable status log), Sprint 4 close: PR #7 build-image CI fix, Task 4.2 Agent registry + semantic cache + kill switches, Sprint 4 Report — Agent Runtime, Chat, First Agent, apps/api/fleet_api/routers/agents_admin.py, Rationale: KillSwitch bytes vs str Redis decoding bug

### Community 100 - "Community 100"
Cohesion: 0.43
Nodes (8): core/langfuse_client.py (LangfuseScorer), core/llm/client.py (LLMClient), core/llm/transport.py (ProxyTransport), Task 4.3 Chat UI (SSE streaming, citations, feedback), apps/api/fleet_api/routers/chat.py, fleet_rag.query.service.answer_query(), Rationale: trace_id/agent_id forwarding gap across LLMClient and answer_query, Web Chat UI (apps/web chat components)

### Community 101 - "Community 101"
Cohesion: 0.25
Nodes (8): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, Fleet AI Operations Platform, Problem Statement, Fleet Vision (single internal platform), Platform-Level Success Metrics, Why This Approach Wins

### Community 102 - "Community 102"
Cohesion: 0.25
Nodes (8): 15-Minute Demo Script, Sprint 10 — Demo Assembly & Docs, 10.2 Docs + Release, 4.4 Support Copilot (Agent #1), Sprint 9 — Hardening, 9.1 Load Testing (k6), 9.2 Security (scan + injection corpus), 9.4 Backup & Restore Drill

### Community 103 - "Community 103"
Cohesion: 0.36
Nodes (8): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.4 Container-to-Host Ollama Reachability, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy, 2.3 Gateway Client (core/llm), 2.4 Budgets

### Community 104 - "Community 104"
Cohesion: 0.25
Nodes (8): FastAPI app factory (create_app), Keycloak aud claim mismatch risk, Cross-cutting middleware (trace_id, audit, rate-limit), OIDC token validation (Keycloak JWKS RS256), RBAC permission service (TRD 7.1 matrix), compose service: redis, Redis Service (Helm), Redis Values (Helm defaults)

### Community 105 - "Community 105"
Cohesion: 0.39
Nodes (8): CI job: build-image (docker build + trivy scan), CI job: integration (pytest tests/integration, testcontainers), CI job: lint (ruff + mypy), CI job: security (bandit + gitleaks), CI job: unit (pytest tests/unit), CI GitHub Actions workflow, gitleaks/gitleaks-action@v2, Trivy scan via aquasec/trivy docker image (not trivy-action)

### Community 106 - "Community 106"
Cohesion: 0.38
Nodes (4): new_trace_id(), Generate a request trace id., Request, Response

### Community 107 - "Community 107"
Cohesion: 0.38
Nodes (7): Control Plane, Dev Agent, Approval Queue (interrupt/resume), RAG Grounding Check, Guardrails & Human-in-the-Loop, Kill Switches, Tool risk_class Classification

### Community 108 - "Community 108"
Cohesion: 0.29
Nodes (7): Self-Service Analytics — Data, Analytics fixture warehouse views, Task 5.2 — Analytics agent (agent #2), Alembic first migration (0001_initial), fleet_readonly read-only DB role, GitHub Actions CI pipeline (lint/unit/integration/security/build), Seed script with analytics fixture views (fixture_sales, fixture_orders)

### Community 109 - "Community 109"
Cohesion: 0.33
Nodes (7): Task 1.1 — Monorepo + dev stack, master_key gates admin/management API, compose service: langfuse, compose service: litellm, compose service: postgres, Postgres Service (Helm), Postgres Values (Helm defaults)

### Community 110 - "Community 110"
Cohesion: 0.29
Nodes (7): Keycloak (OIDC), Web UI (Next.js/TS), Next.js 15 Frontend, AuthN/AuthZ (Keycloak OIDC + RBAC), RBAC Role Matrix, End-User Screens, E2E Tests (Playwright)

### Community 111 - "Community 111"
Cohesion: 0.29
Nodes (7): Microsoft Presidio + TR Recognizers, Embedding Dedup (content_sha256), Loki Structured Logs, Data Classification (sensitivity levels), PII Pipeline (Presidio + TR recognizers), Redaction Downgrade Rule, chunks Table

### Community 112 - "Community 112"
Cohesion: 0.29
Nodes (7): Keycloak fleet realm with five test users, Sprint 1 Stage A Implementation Plan, pre-push git hook (task 1.0), Helm umbrella chart + k3d bootstrap, compose service: keycloak, Keycloak Service (Helm), Keycloak Values (Helm defaults)

### Community 113 - "Community 113"
Cohesion: 0.29
Nodes (7): Ilan Kalitesi SOP fixture (listing-quality-sop.txt), Uyelik ve Odeme SSS fixture (membership-and-payments.txt), Trink sat! Hizli Arac Satis Sureci fixture (trink-sat-process.txt), Rationale: Presidio TR recognizer false-positive on generic nouns, Embedded prompt-injection test phrase (SOP fixture), apps/rag/fleet_rag/seed_docs.py (make seed-docs), Trink sat! (fast guaranteed vehicle sale feature)

### Community 114 - "Community 114"
Cohesion: 0.29
Nodes (6): name, packageManager, private, scripts, build, lint

### Community 117 - "Community 117"
Cohesion: 0.40
Nodes (6): Definition of Done, Doc/Split Sync Contract, Fleet Platform (CLAUDE.md guidance), Mandatory Skills (superpowers + graphify), PROGRESS.md Durable Memory Protocol, Task Execution Protocol

### Community 118 - "Community 118"
Cohesion: 0.53
Nodes (6): core/citations.py (Citation, attach_citations), core/graph.py (build_graph base LangGraph), core/guardrails.py (wrap_untrusted, detect_injection), core/hitl.py (requires_approval), core/memory.py (build_context rolling window), Task 4.1 Runtime core (LangGraph base graph + Postgres checkpointer)

### Community 119 - "Community 119"
Cohesion: 0.33
Nodes (6): Dev setup bootstrap (task 10.1), Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four environments (local/test/demo-staging/prod), Shared Helm chart (per-env values), README.md — fleet-workflow

### Community 120 - "Community 120"
Cohesion: 0.33
Nodes (6): Agent Hub, Control Plane (guardrails, HITL, eval, audit), Fleet — AI Operations Platform (Overview), Knowledge Base (RAG), Support Copilot (Customer Service agent), Workflow Studio (n8n)

### Community 121 - "Community 121"
Cohesion: 0.47
Nodes (6): Budget Hierarchy (global→dept→agent→user), Cost & Token Optimization (§5), Data Model (PostgreSQL core tables, §11), Prompt Caching, Semantic Cache, Spend Ledger

### Community 122 - "Community 122"
Cohesion: 0.40
Nodes (6): Sprint 3 — RAG, 3.1 Ingestion Pipeline, 3.2 Collections + Retention, 3.3 Query + Citations, 3.4 Web Shell + Knowledge UI, 4.3 Chat UI

### Community 123 - "Community 123"
Cohesion: 0.40
Nodes (6): Gateway-Everything Principle, LLM Gateway (LiteLLM Proxy), MCP Servers, Observability Stack (Langfuse/Prometheus/Grafana/Loki), Model Registry, Agent Builder Screen

### Community 124 - "Community 124"
Cohesion: 0.33
Nodes (6): Secure and Observable by Default, Langfuse (self-hosted), Trace ID Correlation, Langfuse LLM Layer (traces/generations), Output Guards (RAG grounding check), Evaluation (golden sets)

### Community 125 - "Community 125"
Cohesion: 0.47
Nodes (6): LiteLLM Proxy, Ollama (dev local models), vLLM (prod GPU), Fallback Chains & Circuit Breaking, Local-Model Lane (pii/confidential), Reference Sizing

### Community 126 - "Community 126"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 127 - "Community 127"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat endpoint's Analytics reply path against the real dev stack (ta, test_analytics_reply_shows_sql_for_a_business_question()

### Community 128 - "Community 128"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat SSE + feedback against the real dev stack (task 4.3 AC: "stre, test_chat_stream_renders_answer_and_feedback_lands_in_langfuse()

### Community 129 - "Community 129"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: `/v1/rag/query` end to end against the real dev-stack (task 3.3 AC, test_rag_query_returns_grounded_answer_with_citations()

### Community 130 - "Community 130"
Cohesion: 0.40
Nodes (4): AsyncEngine, Append-only audit log writes., Insert one append-only audit row. Never updates or deletes., write_audit()

### Community 131 - "Community 131"
Cohesion: 0.50
Nodes (3): Any, Protocol, ReasoningUtilityClient

### Community 133 - "Community 133"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 134 - "Community 134"
Cohesion: 0.40
Nodes (4): JWT, next-auth, next-auth/jwt, Session

### Community 135 - "Community 135"
Cohesion: 0.70
Nodes (5): Sprint 3 Report — RAG (Ingestion, Collections, Query, Web Shell), Sprint 3 Task 3.1 Ingestion pipeline, Sprint 3 Task 3.2 Collections + retention, Sprint 3 Task 3.3 Query + citations, Sprint 3 Task 3.4 Web shell + Knowledge UI

### Community 136 - "Community 136"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 137 - "Community 137"
Cohesion: 0.40
Nodes (5): Security Testing (trivy/bandit/semgrep/ZAP/garak), Prometheus/Grafana Metrics, Prompt Injection Defense (quarantine blocks), Security Tests (garak/injection corpus), Risks & Mitigations

### Community 138 - "Community 138"
Cohesion: 0.40
Nodes (5): Default Model Matrix, Routing & Tiering (utility/reasoning), Model Tiering (utility vs reasoning), Prompt Caching, agents Table

### Community 139 - "Community 139"
Cohesion: 0.50
Nodes (3): _builder_token(), Integration: `/v1/admin/agents` CRUD + pause/resume against the real dev stack, test_agent_crud_and_pause_blocks_a_real_graph_run()

### Community 140 - "Community 140"
Cohesion: 0.50
Nodes (3): configure_tracing(), OpenTelemetry setup (dev: logging exporter) and trace-id helpers., Install a console span exporter once (dev default per plan/TRD §14).

### Community 142 - "Community 142"
Cohesion: 0.50
Nodes (3): TestClient, Unit test: healthz returns ok without any external dependency., test_healthz_ok()

### Community 145 - "Community 145"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 146 - "Community 146"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

### Community 155 - "Community 155"
Cohesion: 1.00
Nodes (3): openapi.json (dumped API schema), packages/shared README — @fleet/shared, src/schema.d.ts (generated, do not hand-edit)

## Ambiguous Edges - Review These
- `Self-Service Analytics Agent (Text-to-SQL)` → `Qdrant Vector DB`  [AMBIGUOUS]
  docs/source/PROJECT_OVERVIEW.md · relation: conceptually_related_to

## Knowledge Gaps
- **252 isolated node(s):** `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)`, `Listing Quality Agent (Listings Ops)`, `Insights Publisher Agent (Marketing)`, `Agent Hub` (+247 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **63 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Self-Service Analytics Agent (Text-to-SQL)` and `Qdrant Vector DB`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `fleet_api/registry.py — model registry` connect `Community 81` to `Community 40`, `Docs & Department Scenarios`, `Model Registry`, `LLM Client Factory`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Why does `LLMClient` connect `Community 52` to `Community 35`, `RAG OCR Pipeline`, `LLM Client Factory`, `LLM Client Unit Tests`, `LLM Gateway Client`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `run_ingestion()` connect `RAG Chunking` to `RAG OCR Pipeline`, `PII Detection & Redaction`, `MinIO Object Store`, `RAG Document Extraction`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `KillSwitch` (e.g. with `AgentIn` and `AgentOut`) actually correct?**
  _`KillSwitch` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `GitHubTool` (e.g. with `ApprovalOut` and `DecisionIn`) actually correct?**
  _`GitHubTool` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `ToolContract` (e.g. with `EmailSender` and `EmailSendTool`) actually correct?**
  _`ToolContract` has 18 INFERRED edges - model-reasoned connections that need verification._
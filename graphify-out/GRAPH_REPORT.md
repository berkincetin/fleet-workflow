# Graph Report - .  (2026-07-23)

## Corpus Check
- 99 files · ~178,444 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2917 nodes · 5391 edges · 268 communities (193 shown, 75 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 1076 edges (avg confidence: 0.68)
- Token cost: 176,451 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Examples Gallery Backend
- Community 9
- Community 10
- Community 11
- Knowledge UI
- Community 13
- Community 14
- Community 15
- Community 16
- OIDC Token Auth
- Community 18
- Community 19
- Admin Pages (Agents/Models/Keys)
- Community 21
- Community 22
- Community 23
- Community 24
- Dealer Onboarding Scenario
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Workflows Router
- Community 38
- Community 39
- App Route Layouts
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- n8n REST Client
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- n8n Automations Sprint (Invoice/Weekly)
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Sprint 6 n8n Tasks + Dept Use Cases
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Root Layout + App Shell
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Wave 1 Department Scenarios
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Examples Try-It Dialogs
- Community 93
- Sprint 6.5 Platform UI Tasks
- Community 95
- Community 96
- Invoice/Weekly-Summary Automation Surface
- Community 98
- Automation Upload Dialogs
- Invoice Agent Pipeline
- Sprint 5-6 Governed Agents Reports
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Examples Gallery Page
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
- n8n Queue Mode + SSO Proxy
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Scenarios Hub Page
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Eval Threshold Config
- Community 134
- Community 135
- Community 136
- Community 137
- Fleet API Key Service
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 148
- Community 149
- Community 150
- Community 151
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 164
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
- Community 188
- Community 189
- Community 190
- Community 191
- Community 192
- Community 193
- Community 194
- Community 195
- Community 196
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
- Community 216
- Community 217
- Community 219
- Community 222
- Community 225
- Community 227
- Community 231
- Community 232
- Community 233
- Community 235
- Community 236
- Community 237
- Community 238
- Community 239
- Community 240
- Community 241
- Community 242
- Community 243
- Community 244
- Community 245
- Community 246
- Community 247
- Community 248
- Community 249
- Community 250
- Community 251
- Community 252
- Community 253
- Community 254
- Community 255
- Community 256
- Community 257
- Community 258
- Community 259
- Community 260
- Community 261
- Community 262
- Community 263
- Community 264
- Community 265

## God Nodes (most connected - your core abstractions)
1. `KillSwitch` - 53 edges
2. `GitHubTool` - 36 edges
3. `ToolContract` - 34 edges
4. `JiraTool` - 34 edges
5. `SlackPostTool` - 33 edges
6. `Settings` - 31 edges
7. `Hit` - 30 edges
8. `PgReadOnlyTool` - 30 edges
9. `ErpTool` - 28 edges
10. `FakeTransport` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Per-model fallback chains` --semantically_similar_to--> `Security: API keys leaked into tracked .env.example`  [INFERRED] [semantically similar]
  gateway/litellm/config.yaml → docs/reports/sprint-2.md
- `_qdrant_up()` --calls--> `qdrant_client_from_env()`  [INFERRED]
  tests/integration/test_rag_stores_live.py → apps/rag/fleet_rag/store/qdrant_store.py
- `test_collection_name_namespaces_by_fleet_collection_id()` --calls--> `collection_name()`  [INFERRED]
  tests/unit/test_rag_qdrant_store.py → apps/rag/fleet_rag/store/qdrant_store.py
- `test_load_dataset_parses_jsonl_into_cases()` --calls--> `load_dataset()`  [INFERRED]
  tests/unit/test_eval_runner.py → evals/runner.py
- `test_case_result_is_a_dataclass_with_id_and_reason()` --calls--> `CaseResult`  [INFERRED]
  tests/unit/test_eval_runner.py → evals/runner.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Sprint 6.5 tasks together turn 6 unbuilt department scenarios into honest coming-soon UI cards backed by real sprint tasks** — docs_implementation_plan_task_6_5_1, docs_implementation_plan_task_6_5_6, docs_implementation_plan_task_8_5, docs_implementation_plan_sprint11, docs_implementation_plan_sprint12, docs_department_scenarios [EXTRACTED 0.90]
- **Four Wave 0 department scenarios that shipped live in Sprints 4-6 (Support Copilot, Analytics, Dev Agent, Invoice Agent)** — docs_department_scenarios_support_copilot, docs_department_scenarios_self_service_analytics, docs_department_scenarios_dev_agent, docs_department_scenarios_invoice_reconciliation [EXTRACTED 1.00]
- **n8n queue-mode compose services (main, worker, oauth2-proxy) forming the SSO-gated automation subsystem** — infra_compose_docker_compose_dev_n8n_main, infra_compose_docker_compose_dev_n8n_worker, infra_compose_docker_compose_dev_n8n_oauth2_proxy, infra_compose_docker_compose_dev_keycloak [EXTRACTED 0.95]
- **HITL Interrupt/Resume/Approval Flow** — core_hitl_module, core_graph_module, approvals_router, dev_agent_graph [INFERRED 0.85]
- **Sprint 3 RAG pipeline stages: ingestion, collections, query/citations, web shell** — docs_reports_sprint_3_md_task_3_1, docs_reports_sprint_3_md_task_3_2, docs_reports_sprint_3_md_task_3_3, docs_reports_sprint_3_md_task_3_4 [EXTRACTED 1.00]
- **Gateway client call orchestration: routing -> transport -> ledger/cost -> budget** — apps_runtime_core_llm_client, apps_runtime_core_llm_routing, apps_runtime_core_llm_transport, apps_runtime_core_llm_ledger, fleet_api_budget [EXTRACTED 0.90]
- **KVKK Sensitivity Routing & Redaction Flow** — docs_source_technical_requirements_pii_pipeline, docs_source_technical_requirements_redaction_downgrade, docs_source_technical_requirements_sensitivity_routing, docs_source_technical_requirements_local_model_lane [EXTRACTED 0.90]
- **LLM Gateway Cost Governance (registry, budgets, spend ledger)** — docs_source_technical_requirements_llm_gateway, docs_source_technical_requirements_model_registry, docs_source_technical_requirements_budget_hierarchy, docs_source_technical_requirements_spend_ledger [EXTRACTED 0.85]
- **Guardrails + HITL External-Write Control** — docs_source_technical_requirements_guardrails_hitl, docs_source_technical_requirements_tool_risk_class, docs_source_technical_requirements_approval_queue, docs_source_technical_requirements_langgraph_runtime [EXTRACTED 0.85]
- **Sprint 1 three-stage delivery (foundation, CI, auth/middleware/helm)** — docs_superpowers_plans_2026_07_15_sprint_1_stage_a_plan, docs_superpowers_plans_2026_07_15_sprint_1_stage_b_plan, docs_superpowers_plans_2026_07_16_sprint_1_stage_c_plan [EXTRACTED 1.00]
- **CI Pipeline: lint -> unit -> {integration, security, build-image}** — github_workflows_ci_job_lint, github_workflows_ci_job_unit, github_workflows_ci_job_integration, github_workflows_ci_job_security, github_workflows_ci_job_build_image [INFERRED 0.85]
- **Fleet k3d/Helm Service Stack (8 templated services)** — infra_helm_fleet_templates_postgres_postgres, infra_helm_fleet_templates_redis_redis, infra_helm_fleet_templates_qdrant_qdrant, infra_helm_fleet_templates_minio_minio, infra_helm_fleet_templates_keycloak_keycloak, infra_helm_fleet_templates_prometheus_prometheus [INFERRED 0.75]
- **Grafana Datasource Provisioning Group** — infra_compose_grafana_provisioning_datasources_datasources_prometheus_datasource, infra_compose_grafana_provisioning_datasources_datasources_loki_datasource, infra_compose_docker_compose_dev_grafana [INFERRED 0.85]
- **Fleet Five Core Modules** — docs_project_overview_agent_hub, docs_project_overview_workflow_studio, docs_project_overview_knowledge_base_rag, docs_project_overview_integration_layer_mcp, docs_project_overview_control_plane [EXTRACTED 1.00]
- **Demo Script Agent Showcase** — docs_split_implementation_plan_sprint_4_runtime_chat_first_agent_task_4_4_support_copilot, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_task_5_5_dev_agent, docs_split_implementation_plan_sprint_6_n8n_automations_task_6_3_invoice_intake, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.90]
- **Cost Governance Stack** — docs_split_technical_requirements_05_cost_token_optimization_budget_hierarchy, docs_split_technical_requirements_05_cost_token_optimization_spend_ledger, docs_split_technical_requirements_05_cost_token_optimization_cost_anomaly_alerts, docs_split_technical_requirements_03_tech_stack_litellm [EXTRACTED 0.85]
- **Guardrails & HITL Approval Flow** — docs_split_technical_requirements_09_guardrails_hitl_tool_risk_class, docs_split_technical_requirements_09_guardrails_hitl_approval_queue, docs_split_technical_requirements_03_tech_stack_langgraph, docs_split_technical_requirements_11_data_model_core_tables [EXTRACTED 0.85]

## Communities (268 total, 75 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (74): CitationOut, AsyncSession, BaseModel, query(), QueryIn, QueryOut, RAG query test harness (task 3.3): `/v1/rag/query`.  A chat-less endpoint that, Answer (+66 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (69): extract_invoice_fields(), ExtractionParseError, InvoiceFields, Any, Exception, Protocol, Invoice text -> structured fields (task 6.3, dept scenario 04 "extracted fields, The model's field-extraction response was malformed or missing a field. (+61 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (59): Model, Model registry (TRD §4.1). Mirrored into the LiteLLM config., build_model_row(), evaluate_smoke(), _is_local(), ModelDraft, probe_model(), Connectivity/capability smoke probe for the model registry (task 2.2).  Runs a (+51 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (46): ApiKeyInvalid, ApiKeyRecord, generate_key(), has_scope(), hash_key(), keys_match(), datetime, Exception (+38 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (36): Chunk, chunk_text(), dedup_chunks(), Structure-aware chunking + content-hash dedup (TRD Sprint 3 task 3.1).  Splits, Pack paragraphs into chunks of at most `max_tokens` words each., Drop chunks whose content hash is already embedded (0 new-embedding re-upload)., _sha256(), EmbeddingClient (+28 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (26): BranchNamePatternError, build_default_backend(), GitHubBackend, Any, Exception, Protocol, github MCP tool: read_repo/create_branch/open_pr (task 5.3, dept scenario 03 De, create_branch was asked to create a name outside the `agent/*` pattern. (+18 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (30): ocr_image(), OcrResult, Any, Protocol, OCR step: vision-LLM primary, tesseract fallback (TRD §3 tech stack, task 3.1)., Run vision-LLM OCR; fall back to `tesseract_fn(image_bytes)` on failure/empty., _try_vision(), VisionClient (+22 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (30): AnalyzerEngine, _analyzer(), apply_pii_policy(), PiiFinding, PiiPolicyError, PolicyResult, Any, ValueError (+22 more)

### Community 8 - "Examples Gallery Backend"
Cohesion: 0.12
Nodes (24): EvalCase, Examples-gallery case (task 6.5.2, TRD §11 deferred eval_datasets shape)., create_example(), ExampleIn, ExampleOut, list_examples(), Any, AsyncSession (+16 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (33): Agent, AgentSummaryOut, _analytics_reply(), _assert_agent_may_read_its_collections(), ConversationIn, ConversationOut, create_conversation(), FeedbackIn (+25 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (15): CacheHit, _cosine(), Protocol, Redis-backed semantic cache (TRD §5).  Opt-in per agent (deterministic Q&A age, RedisLike, SemanticCache, _FakeRedis, core.semantic_cache: Redis-backed semantic cache (task 4.2, TRD §5).  Opt-in p (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (32): CaseResult, evaluate_invoice_case(), _fold(), load_analytics_dataset(), load_dataset(), load_dev_agent_dataset(), _load_dotenv_fallback(), load_invoice_dataset() (+24 more)

### Community 12 - "Knowledge UI"
Cohesion: 0.13
Nodes (22): KnowledgePage(), DocumentStatusBadge(), VARIANT_BY_STATUS, Collection, Document, IN_FLIGHT_STATUSES, KnowledgeBrowser(), UploadForm() (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (19): BudgetChecker, _first_content(), GatewayError, Ledger, _opt_float(), Any, Exception, Protocol (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (21): build_graph(), Compile the base graph for one agent, bound to a checkpointer for resume., _FakeLLMClient, _FakeRedis, _noop_tool(), Any, Runtime base graph (task 4.1). AC: unit with FakeLLM — routing utility-vs- reas, A write:internal tool with autonomy already granted reaches execute_tool     di (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.19
Nodes (22): _client(), FakeLedger, FakeTransport, Gateway client orchestration (task 2.3).  The client is the ONLY place LLM cal, §6 trace correlation: the proxy's Langfuse callback must tag the trace     with, Records calls; returns a canned OpenAI-style body, or raises to simulate     an, test_embeddings_forwards_trace_id_to_transport(), test_embeddings_pii_routes_to_local_model() (+14 more)

### Community 17 - "OIDC Token Auth"
Cohesion: 0.12
Nodes (23): CurrentUser, _extract_roles(), _fetch_jwks(), get_current_user(), OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens., The authenticated principal extracted from a verified token., Verify a raw bearer token string and return the current user, or raise 401., Verify the bearer token and return the current user, or raise 401. (+15 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (24): DevAgentState, TypedDict, assert_diff_size_ok(), assert_no_protected_paths(), assert_ticket_labeled(), DiffTooLargeError, ProtectedPathError, Any (+16 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (22): _clearance(), effective_sensitivity(), Any, Exception, Sensitivity routing — the KVKK guardrail (CLAUDE.md rule 2, TRD §4.3 + §8).  P, Ordered classification: public < internal < confidential < pii (§4.2)., Raised when no model's clearance covers the request's effective sensitivity., Return max(inputs), applying the §8 redaction-downgrade rule.      Content tha (+14 more)

### Community 20 - "Admin Pages (Agents/Models/Keys)"
Cohesion: 0.16
Nodes (15): AgentOut, AgentsAdmin(), ApiKeyOut, ApiKeysAdmin(), AVAILABLE_SCOPES, badgeVariant(), ModelOut, ModelsAdmin() (+7 more)

### Community 21 - "Community 21"
Cohesion: 0.13
Nodes (23): pricing_sync.py keeps prices in sync, _is_local(), _load_litellm_price_map(), main(), PriceValidationError, Any, Exception, Pricing sync for the LiteLLM proxy config (task 2.1).  Keeps the per-token inp (+15 more)

### Community 22 - "Community 22"
Cohesion: 0.13
Nodes (23): get_pg_ro_tool(), get_slack_tool(), pg_query(), PgQueryIn, PgQueryOut, BaseModel, Service-to-Fleet-API surface for automations (task 6.1/6.2, TRD §7.1).  Routes, slack_post() (+15 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (11): PurgeReport, _FakeObjectStore, _FakeSelectResult, _FakeSession, _FakeSessionFactory, _FakeVectorStore, purge_expired orchestration against a fake Postgres session (task 3.2).  Exerc, Mirrors SQLAlchemy's Result: execute() is awaited, .all() on the     returned R (+3 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (20): _build_system_prompt(), ClarificationNeeded, generate_sql(), Any, Exception, NL question -> SQL (task 5.2, dept scenario 02 "SQL gen" call-site, TRD §4.3 re, Some models wrap JSON in a ```json ... ``` fence despite being told not     to;, The model needs one clarifying question before it can write SQL. (+12 more)

### Community 25 - "Dealer Onboarding Scenario"
Cohesion: 0.10
Nodes (25): Dealer Onboarding scenario (Corporate Sales, Wave 2), HR Talent & Onboarding scenario (HR, Wave 0 partial → 1), Legal Document Review scenario (Legal, Wave 2), Sprint 12 — Wave 2 Scenarios, Task 12.1 — Dealer Onboarding (Corporate Sales), Task 12.2 — Legal Document Review (Legal), Task 8.1 — Local-lane quality rehearsal, Task 8.2 — HR CV mini-flow (pii lane) (+17 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (25): Task 1.0 — Git & GitHub bootstrap, Task 3.1 — Ingestion pipeline, Task 3.2 — Collections + retention, Task 3.3 — Query + citations, Task 3.4 — Web shell + Knowledge UI, PROGRESS.md — durable append-only status log, Sprint 1 — Repo, Stack, CI, Gateway, Sprint 2 — LLM Gateway, Model Registry, Budgets (+17 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (23): Agent, Governed agent config (TRD §11, §4.2 tiering, §5 semantic cache, §9 kill switch), AgentIn, AgentOut, create_agent(), delete_agent(), get_agent(), get_global_read_only() (+15 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (18): main(), Seed synthetic data and analytics fixture warehouse views. Idempotent., Analytics demo agent (task 5.2, department scenario 02). No RAG     collections, Dev Agent demo agent (task 5.5, department scenario 03). No RAG     collections, Invoice & Reconciliation demo agent (task 6.3, department scenario 04).     sen, Import evals/datasets/*.jsonl into `eval_cases` (source='seed'), task     6.5.2, Support Copilot demo agent + its cs-help-center/cs-procedures collections     (, seed() (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (14): MCPAuthError, MCPServer, Raised when a call_tool request carries a wrong/missing API key., Registry + dispatcher for one MCP server's tools., test_call_tool_unknown_tool_raises_key_error(), _FakeGitHubBackend, _FakeSender, _FakeSlackSender (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (19): SemanticLayer, AnalyticsClarification, AnalyticsRefusal, AnalyticsResult, ask_analytics(), GovernedQueryTool, Any, Exception (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (17): KillSwitch, Runtime-side enforcement, checked before any graph node runs a step., _Clock, _FakeRedis, datetime, core.killswitch: per-agent pause + global read-only mode (task 4.2, TRD §9)., redis-py returns bytes unless decode_responses=True was set on the     client —, test_agent_is_active_when_not_paused_in_redis() (+9 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (22): AuditLog, Base, Budget, Chunk, Conversation, Department, Feedback, Message (+14 more)

### Community 33 - "Community 33"
Cohesion: 0.14
Nodes (15): build_default_sender(), DisallowedChannelError, Exception, Protocol, slack MCP tool: slack.post via incoming webhook (task 5.3, dept scenario 03)., Target channel is outside the server's allowlist., Real transport: one incoming-webhook URL per Fleet deployment. Slack     incomi, SlackPostTool (+7 more)

### Community 34 - "Community 34"
Cohesion: 0.16
Nodes (18): DevAgentPlan, plan_ticket(), PlanParseError, Any, Exception, Protocol, Ticket -> plan (task 5.5, dept scenario 03 "plan" step, TRD §4.3 reasoning tier, The model's plan response was malformed or missing a required field. (+10 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (13): build_default_backend(), FixtureJiraBackend, IssueNotFoundError, JiraBackend, Any, Exception, Protocol, jira MCP tool: search/get_issue (task 5.3, dept scenario 03 Dev Agent).  # INT (+5 more)

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (19): _app_session_factory(), database_url(), get_engine(), get_session(), async_sessionmaker, AsyncSession, Async database engine, session factory, and URL resolution for the Fleet API., Return the async database URL from FLEET_DATABASE_URL, or the local default. (+11 more)

### Community 37 - "Workflows Router"
Cohesion: 0.22
Nodes (19): activate_workflow(), ActiveIn, _catalog_entry(), deactivate_workflow(), _find_workflow(), _get_meta(), list_catalog(), Any (+11 more)

### Community 38 - "Community 38"
Cohesion: 0.17
Nodes (13): EmailSender, EmailSendTool, InvalidRecipientError, Exception, Protocol, email MCP tool: SMTP sandbox send (task 5.1).  Always write:external (TRD §9 n, Recipient address is malformed or outside the allowed domain set., _FakeSender (+5 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (18): _extension(), _extract_docx(), _extract_pdf(), extract_text(), _extract_txt(), ExtractResult, ValueError, Text extraction from uploaded documents (task 3.1: extract step).  Dispatches (+10 more)

### Community 40 - "App Route Layouts"
Cohesion: 0.16
Nodes (10): AdminLayout(), AutomationsPage(), Home(), WorkflowCard(), WorkflowOut, { handlers, auth, signIn, signOut }, can(), Permission (+2 more)

### Community 41 - "Community 41"
Cohesion: 0.14
Nodes (14): AsyncEngine, Append-only audit log writes., Insert one append-only audit row. Never updates or deletes., write_audit(), AuditMiddleware, RateLimitMiddleware, Cross-cutting ASGI middleware: trace-id, append-only audit, and rate limiting., Assign a trace_id per request and echo it in the response header. (+6 more)

### Community 42 - "Community 42"
Cohesion: 0.24
Nodes (16): build_dev_agent_graph(), KillSwitch, ReasoningClient, _FakeLLM, _FakeSlackSender, _labeled_ticket(), agents.dev_agent.graph: ticket -> plan -> branch -> PR -> Slack, with a single, Caught before shipping: a raised slack.post() (e.g. an unset/invalid     webhoo (+8 more)

### Community 43 - "Community 43"
Cohesion: 0.16
Nodes (15): BudgetExceeded, BudgetStatus, check_budget(), DbBudgetChecker, _period_start(), Any, async_sessionmaker, datetime (+7 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (20): Dev Agent scenario (IT/Engineering, Wave 0), IMPLEMENTATION_PLAN.md — Sprint Backlog, Deferrable Tasks list, Sprint 0 — Prerequisites, Task 5.3 — Jira/GitHub/Slack MCP, Task 5.4 — Approval queue, Task 7.1 — Admin: users/roles, budgets editor, Task 7.2 — Cost dashboard, approvals, audit explorer (+12 more)

### Community 45 - "Community 45"
Cohesion: 0.12
Nodes (20): Fleet Helm Umbrella Chart, Grafana Service (Helm), Keycloak Service (Helm), Loki Service (Helm), MinIO Service (Helm), Helm Install NOTES, Postgres Service (Helm), Prometheus Service (Helm) (+12 more)

### Community 46 - "Community 46"
Cohesion: 0.14
Nodes (14): create_app(), FastAPI, FastAPI application factory., Build and configure the Fleet API application.      Set with_middleware=False, main(), Dump the FastAPI OpenAPI schema to a file for TS client generation., TestClient, Integration test: an audit row is written with the request trace_id, and the ra (+6 more)

### Community 47 - "Community 47"
Cohesion: 0.23
Nodes (16): NonAllowlistedTableError, Query references a table outside the server's allowlist., Query is not a plain read (DML/DDL, or otherwise unsafe)., UnsafeSqlError, _FakeRunner, fleet_mcp.servers.pg_ro: read-only governed-SQL tool (task 5.1, dept scenario 0, test_allowlisted_query_runs_and_returns_rows(), test_auto_limit_appended_when_missing() (+8 more)

### Community 48 - "Community 48"
Cohesion: 0.27
Nodes (18): EvalCase, evaluate_case(), RagAnswer, Run one case through the real Support Copilot RAG pipeline., _run_case(), _answer(), evals.runner: pure per-case assertion checking (task 4.4, TRD §13.4).  Asserti, test_case_result_is_a_dataclass_with_id_and_reason() (+10 more)

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (15): Approval, HITL approval-queue entry for a write:external tool call (TRD §9, §11)., ApprovalOut, decide_approval(), DecisionIn, list_approvals(), _OcrToolAdapter, Any (+7 more)

### Community 50 - "n8n REST Client"
Cohesion: 0.21
Nodes (4): N8nClient, N8nResult, Any, Thin async client over the n8n REST + webhook surfaces (task 6.5.3).  Reached ov

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (15): Rebuild the Dev Agent graph bound to the approval's run_id (thread_id)     agai, _resume_dev_agent_run(), GitHubTool, PgPoLookup, InvoiceAnswer, InvoiceCase, One synthetic invoice (task 6.3, dept scenario 04 evals: field     extraction a, Run one case through the real Invoice Agent graph (6.3) — real     gateway clie (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.16
Nodes (15): ensure_bucket(), minio_client_from_env(), object_key(), Minio, MinIO object store for uploaded documents (TRD §3 tech stack, task 3.1).  Obje, sha256_bytes(), _minio_up(), _qdrant_up() (+7 more)

### Community 53 - "Community 53"
Cohesion: 0.22
Nodes (16): collection_name(), delete_by_document(), ensure_collection(), Any, QdrantClient, qdrant_client_from_env(), Qdrant vector store (TRD §3 tech stack, tasks 3.1/3.3).  One Qdrant collection, Dense kNN search narrowed by an optional keyword (full-text) filter on     chun (+8 more)

### Community 54 - "Community 54"
Cohesion: 0.18
Nodes (15): attach_citations(), Citation, Any, Generic citation carrier for the graph's citation-attach node (TRD §9, §11 messa, Return a copy of response with a serialized citations list attached., AgentSpec, GraphState, TypedDict (+7 more)

### Community 55 - "Community 55"
Cohesion: 0.16
Nodes (15): InvoiceCase, _case(), evals.runner: Invoice Agent eval assertion checking (task 6.3, dept scenario 04, Caught live: a small local vision model reading small rendered Turkish     text, A genuinely mangled read (missing/extra word, unrecognizable     substitution), test_duplicate_fixture_passes_only_when_flagged(), test_fails_on_amount_extraction_mismatch_beyond_tolerance(), test_fails_on_po_number_extraction_mismatch() (+7 more)

### Community 56 - "Community 56"
Cohesion: 0.16
Nodes (8): _default_now(), _is_flag_set(), _pause_key(), datetime, Protocol, Kill switches: per-agent pause + global read-only mode (TRD §9).  Per-agent `s, Current state of the global flag (task 6.5.3 — the Admin UI's         kill-swit, RedisLike

### Community 57 - "Community 57"
Cohesion: 0.25
Nodes (12): LLMClient, LLMResponse, A completed LLM call: the served model, text, token usage, and cost., Governed entry point for LLM calls. Construct once per process with the     mod, _checker(), FakeLedger, FakeTransport, Budget enforcement inside the gateway client (task 2.4).  The client runs a bu (+4 more)

### Community 58 - "Community 58"
Cohesion: 0.17
Nodes (15): annotate_roles(), build_client(), derive_role(), load_active_models(), Any, async_sessionmaker, Build a production LLMClient from settings + the model registry (task 2.3).  L, Map a default-matrix model name to its tier role for routing. (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.19
Nodes (13): build_context(), Context, Any, Protocol, Conversation context budgeting: rolling window + summarized eviction (TRD §5)., The context to feed a call: an optional rolling summary plus recent turns., Split history into (summary of evicted turns, recent verbatim turns)., SummaryClient (+5 more)

### Community 60 - "n8n Automations Sprint (Invoice/Weekly)"
Cohesion: 0.20
Nodes (17): Invoice & Reconciliation scenario (Finance, Wave 0), Task 6.1 — n8n queue mode, Task 6.2 — Automation #1: weekly summary, Task 6.3 — Automation #2: invoice intake, Sprint 6 Report — n8n Automations, Invoice & Reconciliation — Finance, Vehicle Intake — Trink sat!, Sprint 6 — n8n Automations (+9 more)

### Community 61 - "Community 61"
Cohesion: 0.34
Nodes (16): AnalyticsAnswer, AnalyticsCase, evaluate_analytics_case(), Run one case through the real Analytics agent pipeline (5.2)., _run_analytics_case(), evals.runner: Analytics eval assertion checking (task 5.2, dept scenario 02)., test_expect_row_count_fails_on_mismatch(), test_expect_row_count_passes_on_exact_match() (+8 more)

### Community 62 - "Community 62"
Cohesion: 0.12
Nodes (16): openapi-fetch, openapi-typescript, dependencies, openapi-fetch, devDependencies, openapi-typescript, typescript, typescript (+8 more)

### Community 63 - "Community 63"
Cohesion: 0.21
Nodes (14): compute_cost(), parse_usage(), Any, Token-usage parsing and cost computation (TRD §5).  Pure helpers: read an Open, Token counts for one LLM call., Extract token counts from an OpenAI-style response body., Compute USD cost. Cached input tokens are billed at the cached price; the     r, Usage (+6 more)

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (16): dependencies, class-variance-authority, @fleet/shared, next-intl, @radix-ui/react-slot, @radix-ui/react-tabs, @radix-ui/react-toast, tailwind-merge (+8 more)

### Community 65 - "Community 65"
Cohesion: 0.25
Nodes (14): Document, Uploaded source document (TRD §11)., DocumentOut, get_document(), list_documents(), _minio_client(), _object_key(), AsyncSession (+6 more)

### Community 66 - "Community 66"
Cohesion: 0.19
Nodes (10): InternalMockTool, Any, Exception, internal-mock MCP tool: fixture-backed stand-in for an internal API (task 5.1)., No fixture record exists for the given id., RecordNotFoundError, fleet_mcp.servers.internal_mock: fixture-backed internal API mock (task 5.1)., test_contract_declares_read_risk_class() (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.21
Nodes (10): LangfuseScorer, Push a feedback score onto a Langfuse trace (TRD §6, task 4.3 AC: "👍/👎 lands in, score is +1 (thumbs up) or -1 (thumbs down); Langfuse NUMERIC score., AsyncBaseTransport, core.langfuse_client: push a feedback score onto a Langfuse trace (task 4.3, TRD, _RecordingTransport, test_push_score_body_carries_trace_id_and_value(), test_push_score_posts_to_scores_endpoint_with_basic_auth() (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.16
Nodes (10): apps/runtime/core/llm (gateway client), EmbeddingResponse, LLM gateway client — the only place provider LLM calls are made (CLAUDE.md rule, A completed embeddings call: the served model, vectors, usage, cost., Any, async_sessionmaker, Spend-ledger sink (task 2.3, TRD §5).  Appends one row per LLM call to ``spend, Async writer for spend_ledger rows over a SQLAlchemy session factory. (+2 more)

### Community 69 - "Community 69"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, eslint-config-next, @eslint/eslintrc, @types/node, @types/react, @types/react-dom, typescript (+7 more)

### Community 70 - "Sprint 6 n8n Tasks + Dept Use Cases"
Cohesion: 0.19
Nodes (15): Sprint 6 — n8n Automations, 6.1 n8n Queue Mode + API Keys, 6.2 Automation #1 — Weekly Summary, 6.3 Automation #2 — Invoice Intake, Dealer Onboarding Agent (Corporate Sales), Department Use Cases, Document Review Assistant (Legal & Compliance), Insights Publisher (Marketing) (+7 more)

### Community 71 - "Community 71"
Cohesion: 0.25
Nodes (14): MonkeyPatch, _admin_token(), backing_stack(), _client(), keycloak(), _provision_realm(), Integration test: 401 without/with a bad token, 200 with a valid member token,, Real Postgres + Redis so the audit/rate-limit middleware runs for real     inst (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.24
Nodes (10): _FakeLLM, _FakeRunner, _pg_tool(), agents.analytics.service: orchestrates NL question -> SQL -> governed execution, Caught live (test_chat_analytics_live.py): chat.py passes     sensitivity=agent, test_ambiguous_question_raises_clarification(), test_clear_question_returns_sql_and_rows(), test_generated_sql_is_always_surfaced_alongside_rows() (+2 more)

### Community 73 - "Community 73"
Cohesion: 0.38
Nodes (14): _build_app(), _FakeN8nClient, CurrentUser, FastAPI, fleet_api.routers.workflows: friendly n8n catalog + run/activate proxy (task 6.5, Overrides get_current_user (not require_permission's per-call-site     closures, test_builder_can_activate_workflow(), test_catalog_merges_live_n8n_state() (+6 more)

### Community 74 - "Community 74"
Cohesion: 0.27
Nodes (13): ApiKey, Fleet-issued programmatic credential (TRD §7.1, §11) — hashed, scoped, expiring., ApiKeyIn, ApiKeyIssued, ApiKeyOut, issue_api_key(), list_api_keys(), AsyncSession (+5 more)

### Community 75 - "Community 75"
Cohesion: 0.36
Nodes (13): Collection, RAG document collection (TRD §8 data classification, §11)., CollectionIn, CollectionOut, create_collection(), delete_collection(), get_collection(), list_collections() (+5 more)

### Community 76 - "Community 76"
Cohesion: 0.18
Nodes (10): AsyncpgRunner, build_default_runner(), Any, Real QueryRunner for pg_ro.PgReadOnlyTool, over the `fleet_readonly` role (task, Integration: pg_ro MCP tool against the real dev-stack Postgres (task 5.1 AC —, Defense-in-depth: connect exactly as the runner does and confirm the DB     ses, test_live_query_against_fixture_sales_returns_rows(), test_live_query_on_non_allowlisted_table_never_reaches_db() (+2 more)

### Community 77 - "Community 77"
Cohesion: 0.23
Nodes (11): ObjectStore, purge_expired(), purge_expired_cron(), Any, async_sessionmaker, datetime, Protocol, Retention purge job (task 3.2, TRD §8: per-collection retention days; the worke (+3 more)

### Community 78 - "Root Layout + App Shell"
Cohesion: 0.16
Nodes (9): metadata, AppShell(), ToastContext, ToastMessage, ToastProvider(), ToastVariant, variantClass, react (+1 more)

### Community 79 - "Community 79"
Cohesion: 0.14
Nodes (14): Self-Service Analytics scenario (Data, Wave 0), Self-Service Analytics — Data, Analytics fixture warehouse views, Task 5.2 — Analytics agent (agent #2), Keycloak fleet realm with five test users, Alembic first migration (0001_initial), fleet_readonly read-only DB role, GitHub Actions CI pipeline (lint/unit/integration/security/build) (+6 more)

### Community 80 - "Community 80"
Cohesion: 0.41
Nodes (11): ToolContract, _echo(), _make_server(), fleet_mcp.base: MCP server base — tool registry, risk_class, schema validation,, test_call_tool_missing_required_field_raises_validation_error(), test_call_tool_rejects_extra_unschematized_field(), test_call_tool_success_returns_result(), test_call_tool_wrong_api_key_raises_auth_error() (+3 more)

### Community 81 - "Community 81"
Cohesion: 0.31
Nodes (8): JiraTool, _backend(), _FixtureBackend, fleet_mcp.servers.jira: fixture-backed Jira mock + real-config option (task 5.3, test_contracts_declare_read_risk_class(), test_get_issue_raises_on_unknown_key(), test_get_issue_returns_issue_by_key(), test_search_returns_matching_issues()

### Community 82 - "Community 82"
Cohesion: 0.26
Nodes (12): evaluate_budget(), Decide allow/soft/hard for `spent_usd` against `limit_usd`.      No limit (``N, Budget decision logic (task 2.4, TRD §5).  Pure evaluation of spend against a, test_at_hard_limit_is_blocked(), test_at_soft_limit_sets_soft_flag_but_still_allowed(), test_between_soft_and_hard_is_allowed_and_flagged(), test_no_budget_row_is_unlimited(), test_over_hard_limit_is_blocked() (+4 more)

### Community 83 - "Community 83"
Cohesion: 0.18
Nodes (13): Rule 3: External side effects via MCP with risk_class, Non-Negotiable Rules, Rule 4: Retrieved/tool content is untrusted data, Dev Agent (IT / Engineering), Integration Layer (MCP), Approval Queue (LangGraph interrupt/resume), Guardrails & Human-in-the-Loop (§9), LLM-Specific Security (OWASP LLM Top 10, §7.3) (+5 more)

### Community 84 - "Community 84"
Cohesion: 0.18
Nodes (13): Rule 2: Sensitivity routing enforced, Invoice & Reconciliation Agent (Finance), Talent & Onboarding Agent (HR), Vehicle Intake Agent (Trink sat!), Default Model Matrix (§4.2), Failure Behavior & Fallbacks (§4.4), Local-Model Lane (Ollama/vLLM, pii), Model Registry (§4.1) (+5 more)

### Community 85 - "Wave 1 Department Scenarios"
Cohesion: 0.21
Nodes (13): DEPARTMENT_SCENARIOS.md — Department Scenario Playbooks, Generic Onboarding Checklist (any new department, ~3-5 days), Insights Publisher scenario (Marketing, Wave 1), Listing Quality scenario (Listings Ops, Wave 1), Vehicle Intake scenario (Trink sat!, Wave 1), Sprint 11 — Wave 1 Scenarios, Task 11.1 — Listing Quality (Listings Ops), Task 11.2 — Vehicle Intake (Trink sat!) (+5 more)

### Community 86 - "Community 86"
Cohesion: 0.22
Nodes (3): _FakeGitHubBackend, _FakeJiraBackend, Any

### Community 87 - "Community 87"
Cohesion: 0.21
Nodes (12): Analytics Agent (#2), Approval Queue (HITL), apps/api/fleet_api/routers/approvals.py, Rationale: deterministic branch_suffix collision on repeated runs, Dev Agent (#3), agents/dev_agent/graph.py (dedicated LangGraph), Sprint 5 Report — MCP, Agents #2-3, Approvals, servers/github.py (read_repo, create_branch, open_pr, commit_file) (+4 more)

### Community 88 - "Community 88"
Cohesion: 0.20
Nodes (7): MCPValidationError, Any, Exception, MCP server base: tool registry with declared risk_class, schema validation, and, Raised when a call_tool payload fails the tool's input_schema., _validate_schema(), erp MCP tool: create_draft_entry (task 6.3, dept scenario 04 Invoice & Reconcil

### Community 89 - "Community 89"
Cohesion: 0.23
Nodes (9): build_ocr_contract(), build_ocr_tool(), Any, ocr MCP tool: wraps fleet_rag.ingest.ocr for tool-calling agents (task 5.1)., fleet_mcp.servers.ocr: MCP wrapper around fleet_rag.ingest.ocr (task 5.1).  Th, _StubVisionClient, test_ocr_tool_extracts_text_from_base64_image(), test_ocr_tool_falls_back_to_tesseract_on_vision_failure() (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.23
Nodes (9): _clamp_limit(), PgReadOnlyTool, Any, Protocol, QueryRunner, pg_ro MCP tool: governed read-only SQL (task 5.1, dept scenario 02).  Enforces, _referenced_tables(), Expression (+1 more)

### Community 91 - "Community 91"
Cohesion: 0.24
Nodes (6): GitHubLike, JiraLike, Any, Protocol, Dev Agent graph: ticket -> plan -> branch -> PR -> Slack, single HITL interrupt, SlackLike

### Community 92 - "Examples Try-It Dialogs"
Cohesion: 0.24
Nodes (9): DevRunDialog(), TicketOut, ExampleCard(), ExampleOut, exampleTitle(), InvoiceRunDialog(), SelectContent(), SelectItem() (+1 more)

### Community 93 - "Community 93"
Cohesion: 0.18
Nodes (12): Support Copilot scenario (Customer Service, Wave 0), Task 4.1 — Runtime core, Task 4.2 — Agent registry + semantic cache + kill switches, Task 4.3 — Chat UI, Task 4.4 — Support Copilot (agent #1, cloud lane), Task 4.5 [DEFERRABLE] — Agent Builder v1, Legal Document Review — Legal, Support Copilot — Customer Service (+4 more)

### Community 94 - "Sprint 6.5 Platform UI Tasks"
Cohesion: 0.38
Nodes (12): Sprint 6.5 — Platform UI & Scenario Showcase, Task 6.5.1 — Docs restructuring, Task 6.5.10 — E2E + polish pass, Task 6.5.2 — Examples backend, Task 6.5.3 — n8n client + workflows router, Task 6.5.4 — Compose + workflow import, Task 6.5.5 — Session roles + app shell + UI primitives + i18n scaffolding, Task 6.5.6 — Home dashboard + Department hub (+4 more)

### Community 95 - "Community 95"
Cohesion: 0.21
Nodes (12): 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.2 Analytics Agent (Agent #2), 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue, 5.5 Dev Agent (Agent #3) (+4 more)

### Community 96 - "Community 96"
Cohesion: 0.20
Nodes (12): docs/split/technical-requirements/12-screens.md, TECHNICAL_REQUIREMENTS.md — System Design Document, Cost & Token Optimization (§5), Data Model — PostgreSQL core tables (§11), Gateway-everything design principle, Guardrails & Human-in-the-Loop (§9), Model Registry (§4.1), Observability: Logs, Traces, Agent & Model Performance (§6) (+4 more)

### Community 97 - "Invoice/Weekly-Summary Automation Surface"
Cohesion: 0.17
Nodes (11): compilerOptions, declaration, esModuleInterop, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

### Community 98 - "Community 98"
Cohesion: 0.27
Nodes (9): Tool risk_class -> approval-queue decision (TRD §9).  Pure decision logic, no, Return True if a tool call of this risk_class must go through HITL., requires_approval(), core.hitl: tool risk_class -> autonomous vs approval-queue decision (TRD §9)., test_read_tool_never_requires_approval(), test_write_external_always_requires_approval(), test_write_internal_autonomous_when_pass_rate_and_autonomy_both_clear(), test_write_internal_requires_approval_when_autonomy_disabled() (+1 more)

### Community 99 - "Automation Upload Dialogs"
Cohesion: 0.45
Nodes (7): InvoiceUploadDialog(), CreateExampleDialog(), DialogContent(), DialogDescription(), DialogHeader(), DialogTitle(), useToast()

### Community 100 - "Invoice Agent Pipeline"
Cohesion: 0.18
Nodes (11): Agent Hub, Control Plane, Fleet AI Operations Platform, Integration Layer (MCP), Rollout Strategy Phases 0-3, Technology Coverage Map, Workflow Studio (n8n), Self-Service Analytics Agent (+3 more)

### Community 101 - "Sprint 5-6 Governed Agents Reports"
Cohesion: 0.18
Nodes (11): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, Fleet AI Operations Platform, Problem Statement, Fleet Vision (single internal platform), Five Core Modules, Workflow Studio (n8n) (+3 more)

### Community 102 - "Community 102"
Cohesion: 0.24
Nodes (11): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.2 Ollama Host-Native with GPU, 0.4 Container-to-Host Ollama Reachability, Sensitivity Routing Enforcement, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy (+3 more)

### Community 103 - "Community 103"
Cohesion: 0.49
Nodes (10): DevAgentAnswer, DevAgentCase, evaluate_dev_agent_case(), evals.runner: Dev Agent eval assertion checking (task 5.5, dept scenario 03)., test_branch_name_must_start_with_agent_prefix(), test_expect_blocked_fails_when_run_reached_pending_approval(), test_expect_blocked_passes_when_run_was_refused(), test_expect_pending_approval_fails_when_run_was_blocked_instead() (+2 more)

### Community 104 - "Community 104"
Cohesion: 0.27
Nodes (8): AppError, ForbiddenError, install_error_handlers(), FastAPI, Domain error model and FastAPI exception handlers., Base class for domain errors mapped to HTTP responses., Register a handler that renders AppError as a structured JSON body., Exception

### Community 105 - "Community 105"
Cohesion: 0.31
Nodes (9): list_tickets(), AsyncSession, BaseModel, Dev Agent run trigger (task 5.5, dept scenario 03).  `POST /v1/dev-agent/runs`, Fixture tickets for a run-dialog picker (task 6.5.3, examples gallery     try-i, RunIn, RunOut, start_run() (+1 more)

### Community 106 - "Community 106"
Cohesion: 0.24
Nodes (7): ErpTool, Any, fleet_mcp.servers.erp: mock ERP create_draft_entry (task 6.3, dept scenario 04)., test_contract_declares_write_external(), test_create_draft_entry_records_and_returns_a_draft(), test_each_draft_entry_gets_a_unique_id(), ToolContract

### Community 107 - "Community 107"
Cohesion: 0.24
Nodes (6): ProxyTransport, Any, Async transport that POSTs chat completions to the LiteLLM proxy., Send a completion; raise for a non-2xx so the client maps it to GatewayError., Send an embeddings request; raise for non-2xx (mapped to GatewayError)., Stream a completion (TRD §5 "streaming everywhere"). Yields one dict         pe

### Community 108 - "Examples Gallery Page"
Cohesion: 0.29
Nodes (6): AgentSummary, ExampleOut, ExamplesGallery(), TabsContent(), TabsList(), TabsTrigger()

### Community 109 - "Community 109"
Cohesion: 0.20
Nodes (9): name, private, scripts, build, dev, lint, start, typecheck (+1 more)

### Community 110 - "Community 110"
Cohesion: 0.27
Nodes (10): Rule 1: LLM calls only via gateway client, Self-Service Analytics Agent (Text-to-SQL), Design Principles (gateway-everything, K8s-from-day-one), High-Level Architecture, Keycloak OIDC AuthN, LangGraph Agent Runtime (Postgres checkpointer), LLM Gateway (LiteLLM Proxy), Qdrant Vector DB (+2 more)

### Community 111 - "Community 111"
Cohesion: 0.42
Nodes (8): MockTransport, _client_with_transport(), fleet_api.n8n_client: async client over n8n's REST API + webhooks (task 6.5.3)., test_401_surfaces_as_auth_error_not_unreachable(), test_connect_error_surfaces_as_unreachable_not_raised(), test_list_workflows_happy_path(), test_set_active_calls_correct_endpoint(), test_trigger_webhook_json_posts_body()

### Community 112 - "Community 112"
Cohesion: 0.29
Nodes (6): Integration: the runtime base graph against a REAL Postgres checkpointer (task, Always proposes the same write:external tool call, regardless of tier., _Resp, _send_email(), test_graph_interrupt_and_resume_survive_a_real_postgres_checkpoint(), _ToolCallingLLM

### Community 113 - "Community 113"
Cohesion: 0.25
Nodes (5): build_default_sender(), Real SMTP transport for email.EmailSendTool (task 5.1).  Talks to the sandbox, SmtpSender, Integration: email MCP tool against the real mailpit SMTP sandbox (task 5.1 AC, test_live_send_lands_in_mailpit()

### Community 114 - "Community 114"
Cohesion: 0.25
Nodes (9): Commit & Branch Convention, Enable Branch Protection on main (pre-prod item), Production / Release Checklist, Sprint 1 Report — Repo, Stack, CI, Gateway, Environments, CI/CD, Backup (§14), Helm Umbrella Chart (one chart, k3d + prod), Observability (Langfuse, Prometheus, Grafana, Loki), Testing Strategy (§13) (+1 more)

### Community 115 - "Community 115"
Cohesion: 0.25
Nodes (9): Deferrable Tasks List, HITL Interrupt Node, Agent Kill Switches, Sprint 4 — Runtime, Chat, First Agent, 4.1 Runtime Core, 4.2 Agent Registry + Semantic Cache + Kill Switches, 4.5 Agent Builder v1 [DEFERRABLE], 9.3 Chaos-Lite + garak [DEFERRABLE] (+1 more)

### Community 116 - "Community 116"
Cohesion: 0.28
Nodes (9): 10.1 Fresh-Install Rehearsal, docker-compose.dev.yml Stack, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack, 1.2 CI + Migrations + Seed, 1.3 Gateway Auth Core, 1.4 Gateway Cross-Cutting Middleware (+1 more)

### Community 117 - "Community 117"
Cohesion: 0.22
Nodes (7): @playwright/test, devDependencies, @playwright/test, name, private, scripts, test

### Community 118 - "Community 118"
Cohesion: 0.39
Nodes (6): Integration: full Dev Agent chain against the real dev stack + sandbox GitHub r, _set_common_env(), test_approve_path_opens_real_pr_on_sandbox(), test_reject_path_never_opens_a_pr(), test_unlabeled_ticket_is_blocked_before_any_branch_creation(), _token()

### Community 119 - "n8n Queue Mode + SSO Proxy"
Cohesion: 0.39
Nodes (6): Integration: full Invoice Agent chain against the real dev stack (task 6.3 AC:, _render_invoice_image_base64(), _set_common_env(), test_matching_invoice_reaches_approval_queue_with_extracted_fields(), test_reject_path_never_creates_a_draft_entry(), _token()

### Community 120 - "Community 120"
Cohesion: 0.25
Nodes (4): async_sessionmaker, Integration: spend_ledger writes + budget pre-check aggregate against a real Po, _seed_spend(), _sf()

### Community 121 - "Community 121"
Cohesion: 0.25
Nodes (3): _names(), Static validation of the pinned LiteLLM config (task 2.1).  Guards the shape L, test_all_fallback_targets_are_defined_models()

### Community 122 - "Community 122"
Cohesion: 0.32
Nodes (7): Permission, permissions_for(), Role-based access control: roles, permissions, and the enforcement dependency., Union of permissions granted by the user's roles., Dependency factory: allow the request only if the user holds `perm`., require_permission(), StrEnum

### Community 123 - "Community 123"
Cohesion: 0.36
Nodes (7): is_expired(), No retention_days set means the collection is retained forever., Retention purge: which documents are expired (task 3.2, TRD §8).  Pure decisio, test_document_exactly_at_boundary_is_expired(), test_document_older_than_retention_is_expired(), test_document_within_retention_window_is_not_expired(), test_no_retention_days_never_expires()

### Community 124 - "Community 124"
Cohesion: 0.43
Nodes (7): _collection_id(), main(), Any, Seed the Support Copilot demo KB (task 4.4): upload evals/fixtures/support_copil, seed_docs(), _upsert_document(), async_sessionmaker

### Community 125 - "Community 125"
Cohesion: 0.29
Nodes (5): Analytics agent's semantic layer: view/column glossary the SQL generator ground, ViewSpec, agents.analytics.semantic_layer: view/column glossary the SQL generator grounds, test_allowlisted_tables_match_view_names(), test_describe_renders_view_and_column_glossary()

### Community 126 - "Scenarios Hub Page"
Cohesion: 0.39
Nodes (4): ScenarioCard(), Scenario, SCENARIOS, ScenarioStatus

### Community 127 - "Community 127"
Cohesion: 0.25
Nodes (8): 15-Minute Demo Script, Sprint 10 — Demo Assembly & Docs, 10.2 Docs + Release, 4.4 Support Copilot (Agent #1), Sprint 9 — Hardening, 9.1 Load Testing (k6), 9.2 Security (scan + injection corpus), 9.4 Backup & Restore Drill

### Community 128 - "Community 128"
Cohesion: 0.39
Nodes (8): CI job: build-image (docker build + trivy scan), CI job: integration (pytest tests/integration, testcontainers), CI job: lint (ruff + mypy), CI job: security (bandit + gitleaks), CI job: unit (pytest tests/unit), CI GitHub Actions workflow, gitleaks/gitleaks-action@v2, Trivy scan via aquasec/trivy docker image (not trivy-action)

### Community 129 - "Community 129"
Cohesion: 0.43
Nodes (6): AsyncSession, BaseModel, Invoice Agent run trigger (task 6.3, dept scenario 04 Invoice & Reconciliation)., RunIn, RunOut, start_run()

### Community 130 - "Community 130"
Cohesion: 0.33
Nodes (6): point_id_for(), Deterministic point ID so re-embedding the same content upserts in place., Deterministic point-ID helper for the Qdrant store (task 3.1 dedup)., test_collection_name_namespaces_by_fleet_collection_id(), test_point_id_differs_for_different_hash(), test_point_id_is_deterministic_for_same_hash()

### Community 131 - "Community 131"
Cohesion: 0.33
Nodes (7): Sprint 3 — RAG, 3.1 Ingestion Pipeline, 3.2 Collections + Retention, 3.3 Query + Citations, 3.4 Web Shell + Knowledge UI, 4.3 Chat UI, Knowledge Base (RAG)

### Community 132 - "Community 132"
Cohesion: 0.38
Nodes (7): LiteLLM Proxy, Ollama (dev local models), vLLM (prod GPU), Fallback Chains & Circuit Breaking, Budget Hierarchy, Local-Model Lane (pii/confidential), Reference Sizing

### Community 133 - "Eval Threshold Config"
Cohesion: 0.29
Nodes (7): Microsoft Presidio + TR Recognizers, Embedding Dedup (content_sha256), Loki Structured Logs, Data Classification (sensitivity levels), PII Pipeline (Presidio + TR recognizers), Redaction Downgrade Rule, chunks Table

### Community 134 - "Community 134"
Cohesion: 0.29
Nodes (7): Routing & Tiering (utility/reasoning), Model Tiering (utility vs reasoning), Spend Ledger, Retention & Right to Erasure, agents Table, audit_log Table (append-only), PostgreSQL Core Tables

### Community 135 - "Community 135"
Cohesion: 0.33
Nodes (7): Sensitivity Clearance Ordering, Sensitivity Routing (KVKK), OWASP LLM Top 10 Mapping, Approval Queue (HITL), Tool Risk Class, Integration Tests (testcontainers), CI/CD Pipeline (GitHub Actions)

### Community 136 - "Community 136"
Cohesion: 0.29
Nodes (6): name, packageManager, private, scripts, build, lint

### Community 137 - "Community 137"
Cohesion: 0.52
Nodes (6): _build_app(), CurrentUser, FastAPI, GET /v1/dev-agent/tickets (task 6.5.3): fixture ticket picker for the Examples g, test_builder_lists_fixture_tickets(), test_member_cannot_list_tickets()

### Community 138 - "Fleet API Key Service"
Cohesion: 0.33
Nodes (5): configure_tracing(), new_trace_id(), OpenTelemetry setup (dev: logging exporter) and trace-id helpers., Install a console span exporter once (dev default per plan/TRD §14)., Generate a request trace id.

### Community 139 - "Community 139"
Cohesion: 0.40
Nodes (3): AgentSummary, ChatMessage, ChatWindow()

### Community 141 - "Community 141"
Cohesion: 0.40
Nodes (6): Definition of Done, Doc/Split Sync Contract, Fleet Platform (CLAUDE.md guidance), Mandatory Skills (superpowers + graphify), PROGRESS.md Durable Memory Protocol, Task Execution Protocol

### Community 143 - "Community 143"
Cohesion: 0.33
Nodes (6): Dev setup bootstrap (task 10.1), Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four environments (local/test/demo-staging/prod), Shared Helm chart (per-env values), README.md — fleet-workflow

### Community 144 - "Community 144"
Cohesion: 0.33
Nodes (6): Agent Hub, Control Plane (guardrails, HITL, eval, audit), Fleet — AI Operations Platform (Overview), Knowledge Base (RAG), Support Copilot (Customer Service agent), Workflow Studio (n8n)

### Community 145 - "Community 145"
Cohesion: 0.47
Nodes (6): Budget Hierarchy (global→dept→agent→user), Cost & Token Optimization (§5), Data Model (PostgreSQL core tables, §11), Prompt Caching, Semantic Cache, Spend Ledger

### Community 146 - "Community 146"
Cohesion: 0.33
Nodes (6): Everything-is-an-API Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), RAG Service, FastAPI / Python 3.12, LangGraph + Postgres Checkpointer

### Community 147 - "Community 147"
Cohesion: 0.33
Nodes (6): Secure and Observable by Default, Langfuse (self-hosted), Trace ID Correlation, Langfuse LLM Layer (traces/generations), Output Guards (RAG grounding check), Evaluation (golden sets)

### Community 148 - "Community 148"
Cohesion: 0.33
Nodes (6): Keycloak (OIDC), Web UI (Next.js/TS), Next.js 15 Frontend, AuthN/AuthZ (Keycloak OIDC + RBAC), RBAC Role Matrix, E2E Tests (Playwright)

### Community 149 - "Community 149"
Cohesion: 0.33
Nodes (6): n8n (queue mode), Redis, Default Model Matrix, Model Registry, Prompt Caching, Semantic Cache

### Community 150 - "Community 150"
Cohesion: 0.33
Nodes (6): TRD §13.4 Per-agent eval threshold policy, evals/config.yaml (per-agent thresholds), invoice_agent eval config entry (threshold 0.90), Nightly GitHub Actions Workflow, Nightly e2e Job, Nightly eval Job

### Community 151 - "Community 151"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 152 - "Community 152"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat endpoint's Analytics reply path against the real dev stack (t, test_analytics_reply_shows_sql_for_a_business_question()

### Community 153 - "Community 153"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat SSE + feedback against the real dev stack (task 4.3 AC: "stre, test_chat_stream_renders_answer_and_feedback_lands_in_langfuse()

### Community 155 - "Community 155"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: `/v1/rag/query` end to end against the real dev-stack (task 3.3 AC, test_rag_query_returns_grounded_answer_with_citations()

### Community 156 - "Community 156"
Cohesion: 0.50
Nodes (3): Any, Protocol, ReasoningUtilityClient

### Community 158 - "Community 158"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 159 - "Community 159"
Cohesion: 0.40
Nodes (4): JWT, next-auth, next-auth/jwt, Session

### Community 160 - "Community 160"
Cohesion: 0.70
Nodes (5): Sprint 3 Report — RAG (Ingestion, Collections, Query, Web Shell), Sprint 3 Task 3.1 Ingestion pipeline, Sprint 3 Task 3.2 Collections + retention, Sprint 3 Task 3.3 Query + citations, Sprint 3 Task 3.4 Web shell + Knowledge UI

### Community 161 - "Community 161"
Cohesion: 0.40
Nodes (5): Redis 7 + arq Workers, PostgreSQL 16 + pgbouncer, Batch Lane (provider Batch APIs), Stateless Services + HPA, Phase Map (MVP/P2/P3)

### Community 162 - "Community 162"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 163 - "Community 163"
Cohesion: 0.40
Nodes (5): Security Testing (trivy/bandit/semgrep/ZAP/garak), Prometheus/Grafana Metrics, Prompt Injection Defense (quarantine blocks), Security Tests (garak/injection corpus), Risks & Mitigations

### Community 164 - "Community 164"
Cohesion: 0.60
Nodes (4): Alembic environment. Uses a sync psycopg2 URL derived from FLEET_DATABASE_URL., run_migrations_offline(), run_migrations_online(), _sync_url()

### Community 165 - "Community 165"
Cohesion: 0.50
Nodes (3): _builder_token(), Integration: `/v1/admin/agents` CRUD + pause/resume against the real dev stack, test_agent_crud_and_pause_blocks_a_real_graph_run()

### Community 167 - "Community 167"
Cohesion: 0.50
Nodes (3): _builder_token(), Integration: retention purge against the real dev-stack (task 3.2 AC).  AC: pu, test_collections_list_endpoint_live()

### Community 169 - "Community 169"
Cohesion: 0.67
Nodes (3): ChatStreamEvent, parseSseBlock(), streamChatMessage()

### Community 170 - "Community 170"
Cohesion: 0.67
Nodes (4): Gateway-Everything Principle, LLM Gateway (LiteLLM Proxy), MCP Servers, Observability Stack (Langfuse/Prometheus/Grafana/Loki)

### Community 171 - "Community 171"
Cohesion: 0.67
Nodes (3): main(), promote(), Promote UI-created examples (eval_cases.source='user') into the versioned jsonl

### Community 176 - "Community 176"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 177 - "Community 177"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

### Community 188 - "Community 188"
Cohesion: 1.00
Nodes (3): openapi.json (dumped API schema), packages/shared README — @fleet/shared, src/schema.d.ts (generated, do not hand-edit)

## Ambiguous Edges - Review These
- `Self-Service Analytics Agent (Text-to-SQL)` → `Qdrant Vector DB`  [AMBIGUOUS]
  docs/source/PROJECT_OVERVIEW.md · relation: conceptually_related_to

## Knowledge Gaps
- **271 isolated node(s):** `Agent Hub`, `Control Plane`, `Rollout Strategy Phases 0-3`, `Technology Coverage Map`, `Self-Service Analytics Agent` (+266 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **75 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Self-Service Analytics Agent (Text-to-SQL)` and `Qdrant Vector DB`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `fleet_api/registry.py — model registry` connect `Community 2` to `Community 58`, `Community 21`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `Sprint 8 — KVKK Lane` connect `Dealer Onboarding Scenario` to `Community 2`, `Community 44`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `HR Talent & Onboarding — HR` connect `Community 2` to `Dealer Onboarding Scenario`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `KillSwitch` (e.g. with `AgentIn` and `AgentOut`) actually correct?**
  _`KillSwitch` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `GitHubTool` (e.g. with `ApprovalOut` and `DecisionIn`) actually correct?**
  _`GitHubTool` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `ToolContract` (e.g. with `EmailSender` and `EmailSendTool`) actually correct?**
  _`ToolContract` has 18 INFERRED edges - model-reasoned connections that need verification._
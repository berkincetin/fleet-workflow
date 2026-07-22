# Graph Report - .  (2026-07-22)

## Corpus Check
- 81 files · ~154,216 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2702 nodes · 4910 edges · 241 communities (172 shown, 69 thin omitted)
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 1111 edges (avg confidence: 0.69)
- Token cost: 12,000 input · 3,500 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
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
- Invoice/Weekly-Summary Automation Surface
- Community 98
- Community 99
- Invoice Agent Pipeline
- Sprint 5-6 Governed Agents Reports
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
- n8n Queue Mode + SSO Proxy
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
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 176
- Community 177
- Community 178
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
- Community 185
- Community 186
- Community 187
- Community 188
- Community 189
- Community 190
- Community 191
- Community 193
- Community 195
- Community 198
- Community 201
- Community 203
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
- Community 222
- Community 223
- Community 224
- Community 225
- Community 226
- Community 227
- Community 228
- Community 229
- Community 230
- Community 231
- Community 232
- Community 233
- Community 234
- Community 235
- Community 236
- Community 237
- Community 240

## God Nodes (most connected - your core abstractions)
1. `KillSwitch` - 46 edges
2. `SlackPostTool` - 41 edges
3. `GitHubTool` - 39 edges
4. `PgReadOnlyTool` - 38 edges
5. `JiraTool` - 37 edges
6. `ToolContract` - 36 edges
7. `Hit` - 30 edges
8. `ErpTool` - 29 edges
9. `FakeTransport` - 26 edges
10. `PgPoLookup` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Per-model fallback chains` --semantically_similar_to--> `Security: API keys leaked into tracked .env.example`  [INFERRED] [semantically similar]
  gateway/litellm/config.yaml → docs/reports/sprint-2.md
- `test_push_score_raises_on_http_error()` --calls--> `LangfuseScorer`  [INFERRED]
  tests/unit/test_runtime_langfuse_client.py → apps/runtime/core/langfuse_client.py
- `test_case_result_is_a_dataclass_with_id_and_reason()` --calls--> `CaseResult`  [INFERRED]
  tests/unit/test_eval_runner.py → evals/runner.py
- `Rule 1: LLM calls only via gateway client` --conceptually_related_to--> `LLM Gateway (LiteLLM Proxy)`  [INFERRED]
  CLAUDE.md → docs/source/TECHNICAL_REQUIREMENTS.md
- `test_smoke_on_add_marks_reachable_model_active()` --calls--> `ModelDraft`  [INFERRED]
  tests/integration/test_model_smoke_probe.py → apps/api/fleet_api/registry.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Invoice Agent governed pipeline (OCR -> extract -> validate -> HITL -> ERP draft)** — invoice_agent_extractor, invoice_agent_validator, invoice_agent_po_lookup, invoice_agent_graph, fleet_mcp_erp_server [EXTRACTED 0.90]
- **n8n queue-mode automation stack (main + worker + SSO proxy)** — infra_compose_docker_compose_dev_n8n_main, infra_compose_docker_compose_dev_n8n_worker, infra_compose_docker_compose_dev_n8n_oauth2_proxy, infra_compose_docker_compose_dev_keycloak [EXTRACTED 0.90]
- **Fleet API service surface for automations (api keys + service_auth + service router)** — api_keys_module, service_auth_module, service_router, require_user_or_service_scope_dep [EXTRACTED 0.85]
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
- **KVKK Sensitivity Routing Flow** — docs_technical_requirements_pii_pipeline, docs_technical_requirements_redaction_downgrade, docs_technical_requirements_sensitivity_routing, docs_technical_requirements_local_model_lane, docs_technical_requirements_clearance_rules [INFERRED 0.85]
- **Write-External Guardrail & HITL Flow** — docs_technical_requirements_risk_class, docs_technical_requirements_approval_queue, docs_project_overview_control_plane, docs_split_department_scenarios_03_dev_agent_dev_agent [INFERRED 0.75]
- **Fleet Five Core Modules** — docs_project_overview_agent_hub, docs_project_overview_workflow_studio, docs_project_overview_knowledge_base_rag, docs_project_overview_integration_layer_mcp, docs_project_overview_control_plane [EXTRACTED 1.00]
- **KVKK Local Model Lane (no cloud egress for pii)** — docs_split_implementation_plan_sprint_8_kvkk_lane_no_cloud_egress_guarantee, docs_split_implementation_plan_sprint_2_llm_gateway_budgets_sensitivity_routing_enforcement, docs_split_implementation_plan_sprint_0_prerequisites_task_0_2_ollama_gpu, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.85]
- **Demo Script Agent Showcase** — docs_split_implementation_plan_sprint_4_runtime_chat_first_agent_task_4_4_support_copilot, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_task_5_5_dev_agent, docs_split_implementation_plan_sprint_6_n8n_automations_task_6_3_invoice_intake, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.90]
- **Cost Governance Stack** — docs_split_technical_requirements_05_cost_token_optimization_budget_hierarchy, docs_split_technical_requirements_05_cost_token_optimization_spend_ledger, docs_split_technical_requirements_05_cost_token_optimization_cost_anomaly_alerts, docs_split_technical_requirements_03_tech_stack_litellm [EXTRACTED 0.85]
- **Guardrails & HITL Approval Flow** — docs_split_technical_requirements_09_guardrails_hitl_tool_risk_class, docs_split_technical_requirements_09_guardrails_hitl_approval_queue, docs_split_technical_requirements_03_tech_stack_langgraph, docs_split_technical_requirements_11_data_model_core_tables [EXTRACTED 0.85]
- **Agents whose write:external actions are always approval-gated** — agent_dev_agent, agent_invoice_agent, agent_insights_publisher, agent_dealer_onboarding, concept_hitl_approval_queue, concept_risk_class [EXTRACTED 1.00]

## Communities (241 total, 69 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (67): Answer, build_answer(), Citation, Generator, Protocol, Grounded answer + citation guardrail (task 3.3, TRD §9 structural check).  Eve, Return citations if every 1-indexed position resolves to a retrieved hit., _resolve_citations() (+59 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (59): Model, Model registry (TRD §4.1). Mirrored into the LiteLLM config., build_model_row(), evaluate_smoke(), _is_local(), ModelDraft, probe_model(), Connectivity/capability smoke probe for the model registry (task 2.2).  Runs a (+51 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (44): ensure_bucket(), minio_client_from_env(), object_key(), Minio, MinIO object store for uploaded documents (TRD §3 tech stack, task 3.1).  Obje, sha256_bytes(), collection_name(), delete_by_document() (+36 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (36): Chunk, chunk_text(), dedup_chunks(), Structure-aware chunking + content-hash dedup (TRD Sprint 3 task 3.1).  Splits, Pack paragraphs into chunks of at most `max_tokens` words each., Drop chunks whose content hash is already embedded (0 new-embedding re-upload)., _sha256(), EmbeddingClient (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (26): BranchNamePatternError, build_default_backend(), GitHubBackend, Any, Exception, Protocol, github MCP tool: read_repo/create_branch/open_pr (task 5.3, dept scenario 03 De, create_branch was asked to create a name outside the `agent/*` pattern. (+18 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (29): is_expired(), ObjectStore, purge_expired(), purge_expired_cron(), PurgeReport, Any, async_sessionmaker, datetime (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (39): _app_session_factory(), database_url(), get_engine(), get_session(), async_sessionmaker, AsyncSession, Async database engine, session factory, and URL resolution for the Fleet API., Return the async database URL from FLEET_DATABASE_URL, or the local default. (+31 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (33): AsyncpgRunner, Any, Real QueryRunner for pg_ro.PgReadOnlyTool, over the `fleet_readonly` role (task, _clamp_limit(), NonAllowlistedTableError, Any, Protocol, QueryRunner (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (25): KnowledgePage(), metadata, DocumentStatusBadge(), VARIANT_BY_STATUS, Collection, Document, IN_FLIGHT_STATUSES, KnowledgeBrowser() (+17 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (36): Agent, Approval, Governed agent config (TRD §11, §4.2 tiering, §5 semantic cache, §9 kill switch), HITL approval-queue entry for a write:external tool call (TRD §9, §11)., ApprovalOut, decide_approval(), DecisionIn, list_approvals() (+28 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (30): ocr_image(), OcrResult, Any, Protocol, OCR step: vision-LLM primary, tesseract fallback (TRD §3 tech stack, task 3.1)., Run vision-LLM OCR; fall back to `tesseract_fn(image_bytes)` on failure/empty., _try_vision(), VisionClient (+22 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (34): CaseResult, DevAgentAnswer, DevAgentCase, evaluate_dev_agent_case(), load_analytics_dataset(), load_dev_agent_dataset(), _load_dotenv_fallback(), load_invoice_dataset() (+26 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (30): AnalyzerEngine, _analyzer(), apply_pii_policy(), PiiFinding, PiiPolicyError, PolicyResult, Any, ValueError (+22 more)

### Community 13 - "Community 13"
Cohesion: 0.09
Nodes (28): create_app(), FastAPI, FastAPI application factory., Build and configure the Fleet API application.      Set with_middleware=False, main(), Dump the FastAPI OpenAPI schema to a file for TS client generation., MonkeyPatch, TestClient (+20 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (25): annotate_roles(), build_client(), derive_role(), load_active_models(), Any, async_sessionmaker, Build a production LLMClient from settings + the model registry (task 2.3).  L, Map a default-matrix model name to its tier role for routing. (+17 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (15): CacheHit, _cosine(), Protocol, Redis-backed semantic cache (TRD §5).  Opt-in per agent (deterministic Q&A age, RedisLike, SemanticCache, _FakeRedis, core.semantic_cache: Redis-backed semantic cache (task 4.2, TRD §5).  Opt-in p (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (19): build_default_backend(), IssueNotFoundError, JiraBackend, JiraTool, Any, Exception, Protocol, jira MCP tool: search/get_issue (task 5.3, dept scenario 03 Dev Agent).  # INT (+11 more)

### Community 17 - "Community 17"
Cohesion: 0.16
Nodes (21): build_graph(), Compile the base graph for one agent, bound to a checkpointer for resume., _FakeLLMClient, _FakeRedis, _noop_tool(), Any, Runtime base graph (task 4.1). AC: unit with FakeLLM — routing utility-vs- reas, A write:internal tool with autonomy already granted reaches execute_tool     di (+13 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (27): ApiKeyInvalid, ApiKeyRecord, generate_key(), has_scope(), keys_match(), Exception, Fleet API key issuance/validation (task 6.1, TRD §7.1: "hashed, scoped, expiring, Return a new raw key. Shown to the caller once; only its hash is stored. (+19 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 20 - "Community 20"
Cohesion: 0.19
Nodes (22): _client(), FakeLedger, FakeTransport, Gateway client orchestration (task 2.3).  The client is the ONLY place LLM cal, §6 trace correlation: the proxy's Langfuse callback must tag the trace     with, Records calls; returns a canned OpenAI-style body, or raises to simulate     an, test_embeddings_forwards_trace_id_to_transport(), test_embeddings_pii_routes_to_local_model() (+14 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (21): AsyncEngine, Append-only audit log writes., Insert one append-only audit row. Never updates or deletes., write_audit(), get_settings(), Return a fresh Settings instance (call at app creation, not import time)., AuditMiddleware, RateLimitMiddleware (+13 more)

### Community 22 - "Community 22"
Cohesion: 0.13
Nodes (22): _build_system_prompt(), ClarificationNeeded, generate_sql(), Any, Exception, Protocol, NL question -> SQL (task 5.2, dept scenario 02 "SQL gen" call-site, TRD §4.3 re, Some models wrap JSON in a ```json ... ``` fence despite being told not     to; (+14 more)

### Community 23 - "Community 23"
Cohesion: 0.15
Nodes (22): AgentSummaryOut, ConversationIn, ConversationOut, FeedbackIn, get_killswitch(), get_langfuse_scorer(), list_chat_agents(), MessageIn (+14 more)

### Community 24 - "Community 24"
Cohesion: 0.13
Nodes (22): _clearance(), effective_sensitivity(), Any, Exception, Sensitivity routing — the KVKK guardrail (CLAUDE.md rule 2, TRD §4.3 + §8).  P, Ordered classification: public < internal < confidential < pii (§4.2)., Raised when no model's clearance covers the request's effective sensitivity., Return max(inputs), applying the §8 redaction-downgrade rule.      Content tha (+14 more)

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (25): evaluate_invoice_case(), _fold(), InvoiceAnswer, InvoiceCase, Case-fold for substring matching, Turkish-safe: plain str.lower() turns     'İ', Word-for-word fuzzy match, tolerant of OCR-level diacritic noise (ı/i,     ş/s,, One synthetic invoice (task 6.3, dept scenario 04 evals: field     extraction a, _tr_ascii_fold() (+17 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (23): pricing_sync.py keeps prices in sync, _is_local(), _load_litellm_price_map(), main(), PriceValidationError, Any, Exception, Pricing sync for the LiteLLM proxy config (task 2.1).  Keeps the per-token inp (+15 more)

### Community 27 - "Community 27"
Cohesion: 0.14
Nodes (15): ErpTool, Any, GitHubTool, FixtureJiraBackend, # INTEGRATION-POINT: in-memory fixture tickets, keyed by issue key., fleet_mcp.servers.erp: mock ERP create_draft_entry (task 6.3, dept scenario 04)., test_contract_declares_write_external(), test_create_draft_entry_records_and_returns_a_draft() (+7 more)

### Community 28 - "Community 28"
Cohesion: 0.18
Nodes (17): build_invoice_agent_graph(), KillSwitch, ReasoningClient, _FakeErp, _FakeLLM, _FakeOcr, _matching_po_lookup(), Any (+9 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (22): assert_diff_size_ok(), assert_no_protected_paths(), assert_ticket_labeled(), DiffTooLargeError, ProtectedPathError, Any, Exception, Dev Agent guardrails: pure predicates, no I/O (task 5.5, dept scenario 03).  - (+14 more)

### Community 30 - "Community 30"
Cohesion: 0.17
Nodes (17): KillSwitch, Runtime-side enforcement, checked before any graph node runs a step., _Clock, _FakeRedis, datetime, core.killswitch: per-agent pause + global read-only mode (task 4.2, TRD §9)., redis-py returns bytes unless decode_responses=True was set on the     client —, test_agent_is_active_when_not_paused_in_redis() (+9 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (22): AuditLog, Base, Budget, Chunk, Conversation, Department, Feedback, Message (+14 more)

### Community 32 - "Community 32"
Cohesion: 0.16
Nodes (18): DevAgentPlan, plan_ticket(), PlanParseError, Any, Exception, Protocol, Ticket -> plan (task 5.5, dept scenario 03 "plan" step, TRD §4.3 reasoning tier, The model's plan response was malformed or missing a required field. (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (18): extract_invoice_fields(), ExtractionParseError, Any, Exception, Protocol, Invoice text -> structured fields (task 6.3, dept scenario 04 "extracted fields", The model's field-extraction response was malformed or missing a field., ReasoningClient (+10 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (18): InvoiceFields, ErpLike, InvoiceAgentState, OcrLike, Any, Protocol, TypedDict, Invoice Agent graph: invoice image -> OCR -> extract fields -> validate against (+10 more)

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (13): _first_content(), GatewayError, LLMResponse, _opt_float(), Any, Exception, Planning / generation / judgment call-sites (§4.3)., Classification / extraction / routing / summarization call-sites (§4.3). (+5 more)

### Community 36 - "Community 36"
Cohesion: 0.13
Nodes (15): MCPAuthError, MCPServer, MCPValidationError, Any, Exception, MCP server base: tool registry with declared risk_class, schema validation, and, Raised when a call_tool request carries a wrong/missing API key., Raised when a call_tool payload fails the tool's input_schema. (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.14
Nodes (22): Agent Hub, Control Plane, Fleet AI Operations Platform, Integration Layer (MCP), Rollout Strategy Phases 0-3, Technology Coverage Map, Workflow Studio (n8n), Department Scenarios Wave Plan & Spec Template (+14 more)

### Community 38 - "Community 38"
Cohesion: 0.23
Nodes (21): EvalCase, evaluate_case(), load_dataset(), RagAnswer, Run one case through the real Support Copilot RAG pipeline., Returns (results, pass_rate, threshold)., run_agent_eval(), _run_case() (+13 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (18): _extension(), _extract_docx(), _extract_pdf(), extract_text(), _extract_txt(), ExtractResult, ValueError, Text extraction from uploaded documents (task 3.1: extract step).  Dispatches (+10 more)

### Community 40 - "Community 40"
Cohesion: 0.17
Nodes (20): Agent, _analytics_reply(), _assert_agent_may_read_its_collections(), create_conversation(), _get_or_create_user(), Any, AsyncSession, CurrentUser (+12 more)

### Community 41 - "Community 41"
Cohesion: 0.19
Nodes (19): AgentIn, AgentOut, create_agent(), delete_agent(), get_agent(), get_killswitch(), list_agents(), pause_agent() (+11 more)

### Community 42 - "Community 42"
Cohesion: 0.16
Nodes (15): BudgetExceeded, BudgetStatus, check_budget(), DbBudgetChecker, _period_start(), Any, async_sessionmaker, datetime (+7 more)

### Community 43 - "Community 43"
Cohesion: 0.12
Nodes (20): Fleet Helm Umbrella Chart, Grafana Service (Helm), Keycloak Service (Helm), Loki Service (Helm), MinIO Service (Helm), Helm Install NOTES, Postgres Service (Helm), Prometheus Service (Helm) (+12 more)

### Community 44 - "Community 44"
Cohesion: 0.22
Nodes (16): hash_key(), Deterministic hash for storage/lookup — SHA-256 (not bcrypt: this is a     high-, _build_app(), _FakeApiKeyRow, CurrentUser, FastAPI, fleet_api.service_auth: X-Fleet-Api-Key auth + require_user_or_service_scope (ta, Both credentials present: the bearer token path wins, per     require_user_or_se (+8 more)

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (14): apps/runtime/core/llm (gateway client), BudgetChecker, EmbeddingResponse, Ledger, Protocol, LLM gateway client — the only place provider LLM calls are made (CLAUDE.md rule, Sends a chat completion to the proxy and returns the raw response body., Persists a spend_ledger row. (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.29
Nodes (18): AnalyticsAnswer, AnalyticsCase, evaluate_analytics_case(), Run one case through the real Analytics agent pipeline (5.2)., Returns (results, pass_rate, threshold). Same shape as run_agent_eval()     but, _run_analytics_case(), run_analytics_eval(), evals.runner: Analytics eval assertion checking (task 5.2, dept scenario 02). (+10 more)

### Community 47 - "Community 47"
Cohesion: 0.18
Nodes (16): CurrentUser, _extract_roles(), _fetch_jwks(), get_current_user(), OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens., The authenticated principal extracted from a verified token., Verify a raw bearer token string and return the current user, or raise 401., Verify the bearer token and return the current user, or raise 401. (+8 more)

### Community 48 - "Community 48"
Cohesion: 0.22
Nodes (11): EmailSendTool, InvalidRecipientError, Exception, email MCP tool: SMTP sandbox send (task 5.1).  Always write:external (TRD §9 n, Recipient address is malformed or outside the allowed domain set., _FakeSender, fleet_mcp.servers.email: SMTP sandbox tool (task 5.1).  write:external risk_cl, test_email_tool_contract_declares_write_external() (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (15): attach_citations(), Citation, Any, Generic citation carrier for the graph's citation-attach node (TRD §9, §11 messa, Return a copy of response with a serialized citations list attached., AgentSpec, GraphState, TypedDict (+7 more)

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (11): build_dev_agent_graph(), DevAgentState, GitHubLike, JiraLike, Any, KillSwitch, Protocol, ReasoningClient (+3 more)

### Community 51 - "Community 51"
Cohesion: 0.19
Nodes (13): build_context(), Context, Any, Protocol, Conversation context budgeting: rolling window + summarized eviction (TRD §5)., The context to feed a call: an optional rolling summary plus recent turns., Split history into (summary of evicted turns, recent verbatim turns)., SummaryClient (+5 more)

### Community 52 - "Community 52"
Cohesion: 0.12
Nodes (16): openapi-fetch, openapi-typescript, dependencies, openapi-fetch, devDependencies, openapi-typescript, typescript, typescript (+8 more)

### Community 53 - "Community 53"
Cohesion: 0.27
Nodes (13): _FakeLLM, _FakeSlackSender, _labeled_ticket(), agents.dev_agent.graph: ticket -> plan -> branch -> PR -> Slack, with a single, Caught before shipping: a raised slack.post() (e.g. an unset/invalid     webhoo, test_approve_resumes_and_opens_pr_and_notifies_slack(), test_oversized_diff_never_creates_branch(), test_plan_touching_protected_path_never_creates_branch() (+5 more)

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (11): ToolContract, _echo(), _make_server(), fleet_mcp.base: MCP server base — tool registry, risk_class, schema validation,, test_call_tool_missing_required_field_raises_validation_error(), test_call_tool_rejects_extra_unschematized_field(), test_call_tool_success_returns_result(), test_call_tool_wrong_api_key_raises_auth_error() (+3 more)

### Community 55 - "Community 55"
Cohesion: 0.21
Nodes (14): compute_cost(), parse_usage(), Any, Token-usage parsing and cost computation (TRD §5).  Pure helpers: read an Open, Token counts for one LLM call., Extract token counts from an OpenAI-style response body., Compute USD cost. Cached input tokens are billed at the cached price; the     r, Usage (+6 more)

### Community 56 - "Community 56"
Cohesion: 0.15
Nodes (16): Sprint 2 — LLM Gateway, Model Registry, Budgets, Task 2.1 — LiteLLM proxy, Task 2.2 — Model registry, Task 2.3 — Gateway client (core/llm), Task 2.4 — Budgets, Budget Hierarchy, Sensitivity Clearance Rules, Cost & Token Optimization (+8 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (16): Rollout Modes (assist/supervised/autonomous), Generic Department Onboarding Checklist, PostgreSQL Data Model, TRD Design Principles, Environments, CI/CD, Backup, Langfuse LLM Observability, Observability (Logs/Traces/Metrics), Capability Phase Map (CORE/P2/P3) (+8 more)

### Community 58 - "Community 58"
Cohesion: 0.25
Nodes (14): Document, Uploaded source document (TRD §11)., DocumentOut, get_document(), list_documents(), _minio_client(), _object_key(), AsyncSession (+6 more)

### Community 59 - "Community 59"
Cohesion: 0.19
Nodes (10): InternalMockTool, Any, Exception, internal-mock MCP tool: fixture-backed stand-in for an internal API (task 5.1)., No fixture record exists for the given id., RecordNotFoundError, fleet_mcp.servers.internal_mock: fixture-backed internal API mock (task 5.1)., test_contract_declares_read_risk_class() (+2 more)

### Community 60 - "Community 60"
Cohesion: 0.18
Nodes (7): _default_now(), _is_flag_set(), _pause_key(), datetime, Protocol, Kill switches: per-agent pause + global read-only mode (TRD §9).  Per-agent `s, RedisLike

### Community 61 - "Community 61"
Cohesion: 0.29
Nodes (10): LLMClient, Governed entry point for LLM calls. Construct once per process with the     mod, _checker(), FakeLedger, FakeTransport, Budget enforcement inside the gateway client (task 2.4).  The client runs a bu, test_hard_stop_blocks_call_and_bills_nothing(), test_no_checker_means_no_enforcement() (+2 more)

### Community 62 - "Community 62"
Cohesion: 0.13
Nodes (15): dependencies, class-variance-authority, clsx, next-intl, @radix-ui/react-select, @radix-ui/react-slot, tailwind-merge, tailwindcss (+7 more)

### Community 63 - "Community 63"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, eslint-config-next, @eslint/eslintrc, @types/node, @types/react, @types/react-dom, typescript (+7 more)

### Community 64 - "Community 64"
Cohesion: 0.14
Nodes (15): Deferrable Tasks List, HITL Interrupt Node, Agent Kill Switches, Sprint 4 — Runtime, Chat, First Agent, 4.1 Runtime Core, 4.2 Agent Registry + Semantic Cache + Kill Switches, 4.5 Agent Builder v1 [DEFERRABLE], Sprint 7 — Admin & Observability (+7 more)

### Community 65 - "Community 65"
Cohesion: 0.24
Nodes (10): _FakeLLM, _FakeRunner, _pg_tool(), agents.analytics.service: orchestrates NL question -> SQL -> governed execution, Caught live (test_chat_analytics_live.py): chat.py passes     sensitivity=agent, test_ambiguous_question_raises_clarification(), test_clear_question_returns_sql_and_rows(), test_generated_sql_is_always_surfaced_alongside_rows() (+2 more)

### Community 66 - "Community 66"
Cohesion: 0.29
Nodes (13): ApiKey, Fleet-issued programmatic credential (TRD §7.1, §11) — hashed, scoped, expiring., ApiKeyIn, ApiKeyIssued, ApiKeyOut, issue_api_key(), list_api_keys(), AsyncSession (+5 more)

### Community 67 - "Community 67"
Cohesion: 0.36
Nodes (13): Collection, RAG document collection (TRD §8 data classification, §11)., CollectionIn, CollectionOut, create_collection(), delete_collection(), get_collection(), list_collections() (+5 more)

### Community 68 - "Community 68"
Cohesion: 0.26
Nodes (13): get_slack_tool(), pg_query(), PgQueryIn, PgQueryOut, BaseModel, Service-to-Fleet-API surface for automations (task 6.1/6.2, TRD §7.1).  Routes h, slack_post(), SlackPostIn (+5 more)

### Community 69 - "Community 69"
Cohesion: 0.21
Nodes (11): AnalyticsResult, ask_analytics(), GovernedQueryTool, Any, Protocol, ReasoningClient, Analytics agent orchestration: NL question -> SQL -> governed execution (task 5, GovernedToolRefusal (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.15
Nodes (14): Everything-is-an-API Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), n8n (queue mode), RAG Service, Redis, Redis 7 + arq Workers, FastAPI / Python 3.12 (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.19
Nodes (12): Self-Service Analytics Agent (Data), Dealer Onboarding Agent (Corporate Sales), Dev Agent (IT/Engineering), HR Talent & Onboarding Agent(s) (HR), Insights Publisher Agent (Marketing), Invoice & Reconciliation Agent (Finance), Legal Document Review Agent (Legal), Listing Quality Agent (Listings Ops) (+4 more)

### Community 72 - "Community 72"
Cohesion: 0.27
Nodes (11): Application settings, loaded from the environment (pydantic-settings)., Environment-driven configuration for the Fleet API., Settings, CitationOut, AsyncSession, BaseModel, query(), QueryIn (+3 more)

### Community 73 - "Community 73"
Cohesion: 0.19
Nodes (6): Any, Protocol, QueryTool, Real PO lookup over pg_ro (task 6.3, dept scenario 04 "pg_ro.query purchase-orde, PurchaseOrder, _FakePoLookup

### Community 74 - "Community 74"
Cohesion: 0.49
Nodes (12): validate_invoice(), _FakePoLookup, _fields(), _po(), agents.invoice_agent.validator: extracted fields -> validation against purchase, test_amount_mismatch_is_flagged_never_silently_ok(), test_duplicate_po_number_is_flagged(), test_matching_invoice_validates_ok() (+4 more)

### Community 75 - "Community 75"
Cohesion: 0.26
Nodes (12): evaluate_budget(), Decide allow/soft/hard for `spent_usd` against `limit_usd`.      No limit (``N, Budget decision logic (task 2.4, TRD §5).  Pure evaluation of spend against a, test_at_hard_limit_is_blocked(), test_at_soft_limit_sets_soft_flag_but_still_allowed(), test_between_soft_and_hard_is_allowed_and_flagged(), test_no_budget_row_is_unlimited(), test_over_hard_limit_is_blocked() (+4 more)

### Community 76 - "Community 76"
Cohesion: 0.21
Nodes (8): AgentSummary, ChatMessage, ChatWindow(), FeedbackButtons(), FeedbackState, ChatStreamEvent, parseSseBlock(), streamChatMessage()

### Community 77 - "Community 77"
Cohesion: 0.18
Nodes (13): Rule 3: External side effects via MCP with risk_class, Non-Negotiable Rules, Rule 4: Retrieved/tool content is untrusted data, Dev Agent (IT / Engineering), Integration Layer (MCP), Approval Queue (LangGraph interrupt/resume), Guardrails & Human-in-the-Loop (§9), LLM-Specific Security (OWASP LLM Top 10, §7.3) (+5 more)

### Community 78 - "Community 78"
Cohesion: 0.18
Nodes (13): Rule 2: Sensitivity routing enforced, Invoice & Reconciliation Agent (Finance), Talent & Onboarding Agent (HR), Vehicle Intake Agent (Trink sat!), Default Model Matrix (§4.2), Failure Behavior & Fallbacks (§4.4), Local-Model Lane (Ollama/vLLM, pii), Model Registry (§4.1) (+5 more)

### Community 79 - "Community 79"
Cohesion: 0.15
Nodes (13): Self-Service Analytics — Data, Analytics fixture warehouse views, Task 5.2 — Analytics agent (agent #2), Keycloak fleet realm with five test users, Alembic first migration (0001_initial), fleet_readonly read-only DB role, GitHub Actions CI pipeline (lint/unit/integration/security/build), Seed script with analytics fixture views (fixture_sales, fixture_orders) (+5 more)

### Community 80 - "Community 80"
Cohesion: 0.22
Nodes (13): Sprint 1 — Repo, Stack, CI, Gateway, Task 1.1 — Monorepo + dev stack, Task 1.2 — CI + migrations + seed, Task 1.3 — Gateway auth core, Task 1.4 — Gateway cross-cutting middleware, Task 1.5 — Helm umbrella chart skeleton + k3d bootstrap, Sprint 1 Stage A Implementation Plan, pre-push git hook (task 1.0) (+5 more)

### Community 81 - "Community 81"
Cohesion: 0.21
Nodes (13): MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue, 5.5 Dev Agent (Agent #3), write:external Approval Classification, Control Plane (+5 more)

### Community 82 - "Community 82"
Cohesion: 0.18
Nodes (13): Sensitivity Clearance Ordering, Sensitivity Routing (KVKK), Budget Hierarchy, Spend Ledger, OWASP LLM Top 10 Mapping, Retention & Right to Erasure, Approval Queue (HITL), Tool Risk Class (+5 more)

### Community 83 - "Community 83"
Cohesion: 0.22
Nodes (3): _FakeGitHubBackend, _FakeJiraBackend, Any

### Community 84 - "Community 84"
Cohesion: 0.23
Nodes (9): build_ocr_contract(), build_ocr_tool(), Any, ocr MCP tool: wraps fleet_rag.ingest.ocr for tool-calling agents (task 5.1)., fleet_mcp.servers.ocr: MCP wrapper around fleet_rag.ingest.ocr (task 5.1).  Th, _StubVisionClient, test_ocr_tool_extracts_text_from_base64_image(), test_ocr_tool_falls_back_to_tesseract_on_vision_failure() (+1 more)

### Community 85 - "Community 85"
Cohesion: 0.17
Nodes (12): 15-Minute Demo Script, Sprint 0 — Prerequisites, Fleet Implementation Plan (Sprint Backlog), Invoice & Reconciliation — Finance, Vehicle Intake — Trink sat!, Sprint 10 — Demo Assembly & Docs, Sprint 3 — RAG, Sprint 6 — n8n Automations (+4 more)

### Community 86 - "Community 86"
Cohesion: 0.23
Nodes (12): 5.2 Analytics Agent (Agent #2), 6.3 Automation #2 — Invoice Intake, Knowledge Base (RAG), Dealer Onboarding Agent (Corporate Sales), Department Use Cases, Document Review Assistant (Legal & Compliance), Invoice & Reconciliation Agent (Finance), Listing Quality Agent (+4 more)

### Community 87 - "Community 87"
Cohesion: 0.17
Nodes (11): compilerOptions, declaration, esModuleInterop, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

### Community 88 - "Community 88"
Cohesion: 0.22
Nodes (10): get_current_service_key(), _lookup(), AsyncSession, FastAPI dependency for Fleet-issued API-key auth (task 6.1, TRD §7.1).  Parallel, Validate the `X-Fleet-Api-Key` header, or raise 401., Dependency factory: allow the request only if the key holds `scope`., Dependency factory: allow the request if EITHER a Keycloak bearer     token carr, require_scope() (+2 more)

### Community 89 - "Community 89"
Cohesion: 0.24
Nodes (6): Analytics agent's semantic layer: view/column glossary the SQL generator ground, SemanticLayer, ViewSpec, agents.analytics.semantic_layer: view/column glossary the SQL generator grounds, test_allowlisted_tables_match_view_names(), test_describe_renders_view_and_column_glossary()

### Community 90 - "Community 90"
Cohesion: 0.27
Nodes (9): Tool risk_class -> approval-queue decision (TRD §9).  Pure decision logic, no, Return True if a tool call of this risk_class must go through HITL., requires_approval(), core.hitl: tool risk_class -> autonomous vs approval-queue decision (TRD §9)., test_read_tool_never_requires_approval(), test_write_external_always_requires_approval(), test_write_internal_autonomous_when_pass_rate_and_autonomy_both_clear(), test_write_internal_requires_approval_when_autonomy_disabled() (+1 more)

### Community 91 - "Community 91"
Cohesion: 0.20
Nodes (11): Dev Agent — IT / Engineering, Legal Document Review — Legal, Support Copilot — Customer Service, Wave Plan Overview, Deferrable Tasks, Demo Script (15 min), Sprint 4 — Agent Runtime, Chat, First Agent, Sprint 5 — MCP, Agents #2-3, Approvals (+3 more)

### Community 92 - "Community 92"
Cohesion: 0.20
Nodes (11): 15-Minute Demo Script, Sprint 10 — Demo Assembly & Docs, 10.2 Docs + Release, Sprint 3 — RAG, 3.1 Ingestion Pipeline, 3.2 Collections + Retention, 3.3 Query + Citations, 3.4 Web Shell + Knowledge UI (+3 more)

### Community 93 - "Community 93"
Cohesion: 0.27
Nodes (8): AppError, ForbiddenError, install_error_handlers(), FastAPI, Domain error model and FastAPI exception handlers., Base class for domain errors mapped to HTTP responses., Register a handler that renders AppError as a structured JSON body., Exception

### Community 94 - "Community 94"
Cohesion: 0.22
Nodes (6): build_default_sender(), Protocol, slack MCP tool: slack.post via incoming webhook (task 5.3, dept scenario 03)., Real transport: one incoming-webhook URL per Fleet deployment. Slack     incomi, SlackWebhookSender, WebhookSender

### Community 95 - "Community 95"
Cohesion: 0.20
Nodes (9): name, private, scripts, build, dev, lint, start, typecheck (+1 more)

### Community 96 - "Community 96"
Cohesion: 0.27
Nodes (10): Rule 1: LLM calls only via gateway client, Self-Service Analytics Agent (Text-to-SQL), Design Principles (gateway-everything, K8s-from-day-one), High-Level Architecture, Keycloak OIDC AuthN, LangGraph Agent Runtime (Postgres checkpointer), LLM Gateway (LiteLLM Proxy), Qdrant Vector DB (+2 more)

### Community 97 - "Invoice/Weekly-Summary Automation Surface"
Cohesion: 0.20
Nodes (10): PROGRESS 6.2 Weekly summary automation (Cron -> pg_ro -> Slack), Sprint 6 task 6.2: Weekly summary automation, Makefile COMPOSE missing --env-file .env (Sprint-1-era latent bug), apps/api/fleet_api/routers/invoice_agent.py (POST /v1/invoice-agent/runs), n8n webhook 404 despite active:true -- missing webhookId field, require_user_or_service_scope() dual-auth dependency, apps/api/fleet_api/service_auth.py (X-Fleet-Api-Key dependency), apps/api/fleet_api/routers/service.py (Fleet API surface for automations) (+2 more)

### Community 98 - "Community 98"
Cohesion: 0.27
Nodes (10): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, 0.4 Container-to-Host Ollama Reachability, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy, 2.3 Gateway Client (core/llm) (+2 more)

### Community 99 - "Community 99"
Cohesion: 0.29
Nodes (6): Integration: the runtime base graph against a REAL Postgres checkpointer (task, Always proposes the same write:external tool call, regardless of tier., _Resp, _send_email(), test_graph_interrupt_and_resume_survive_a_real_postgres_checkpoint(), _ToolCallingLLM

### Community 100 - "Invoice Agent Pipeline"
Cohesion: 0.31
Nodes (9): apps/runtime/agents/invoice_agent package, PROGRESS 6.3 Invoice intake automation (Invoice Agent), fixture_purchase_orders view (15 rows, seed.py), apps/mcp/fleet_mcp/servers/erp.py (create_draft_entry, always write:external), agents/invoice_agent/extractor.py (extract_invoice_fields, reasoning-tier), agents/invoice_agent/graph.py (dedicated LangGraph pipeline), agents/invoice_agent/po_lookup.py (PgPoLookup, never interpolates untrusted po_number), agents/invoice_agent/validator.py (pure validate_invoice) (+1 more)

### Community 101 - "Sprint 5-6 Governed Agents Reports"
Cohesion: 0.28
Nodes (9): Analytics Agent (#2), Approval Queue (HITL), apps/api/fleet_api/routers/approvals.py, Dev Agent (#3), Sprint 5 Report — MCP, Agents #2-3, Approvals, Sprint 6 Report — n8n Automations, Sprint 6 task 6.1: n8n queue mode + SSO proxy + API keys, Sprint 6 task 6.3: Invoice intake automation (Invoice Agent) (+1 more)

### Community 102 - "Community 102"
Cohesion: 0.25
Nodes (5): build_default_sender(), Real SMTP transport for email.EmailSendTool (task 5.1).  Talks to the sandbox, SmtpSender, Integration: email MCP tool against the real mailpit SMTP sandbox (task 5.1 AC, test_live_send_lands_in_mailpit()

### Community 103 - "Community 103"
Cohesion: 0.39
Nodes (6): PgPoLookup, _FakeQueryTool, agents.invoice_agent.po_lookup: PgPoLookup over a pg_ro-shaped QueryTool (task 6, test_lookup_finds_matching_po(), test_lookup_never_interpolates_the_untrusted_po_number_into_sql(), test_lookup_returns_none_for_unknown_po()

### Community 104 - "Community 104"
Cohesion: 0.25
Nodes (9): Commit & Branch Convention, Enable Branch Protection on main (pre-prod item), Production / Release Checklist, Sprint 1 Report — Repo, Stack, CI, Gateway, Environments, CI/CD, Backup (§14), Helm Umbrella Chart (one chart, k3d + prod), Observability (Langfuse, Prometheus, Grafana, Loki), Testing Strategy (§13) (+1 more)

### Community 105 - "Community 105"
Cohesion: 0.36
Nodes (9): Knowledge Base (RAG), Sprint 8 — KVKK Lane, Support Copilot Agent, HR Talent & Onboarding Agent, Dealer Onboarding Agent, Legal Document Review Agent, Local-Model Lane (Ollama/vLLM), Privacy & KVKK (+1 more)

### Community 106 - "Community 106"
Cohesion: 0.25
Nodes (9): 0.2 Ollama Host-Native with GPU, Sensitivity Routing Enforcement, No Cloud Egress Guarantee (pii lane), Sprint 8 — KVKK Lane, 8.1 Local-Lane Quality Rehearsal, 8.2 HR CV Mini-Flow (pii lane), 8.3 Erasure + Clearance Surfacing, 8.4 PII Masking Verification (+1 more)

### Community 107 - "Community 107"
Cohesion: 0.28
Nodes (9): 10.1 Fresh-Install Rehearsal, docker-compose.dev.yml Stack, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack, 1.2 CI + Migrations + Seed, 1.3 Gateway Auth Core, 1.4 Gateway Cross-Cutting Middleware (+1 more)

### Community 108 - "Community 108"
Cohesion: 0.22
Nodes (7): @playwright/test, devDependencies, @playwright/test, name, private, scripts, test

### Community 109 - "Community 109"
Cohesion: 0.39
Nodes (6): Integration: full Dev Agent chain against the real dev stack + sandbox GitHub r, _set_common_env(), test_approve_path_opens_real_pr_on_sandbox(), test_reject_path_never_opens_a_pr(), test_unlabeled_ticket_is_blocked_before_any_branch_creation(), _token()

### Community 110 - "Community 110"
Cohesion: 0.39
Nodes (6): Integration: full Invoice Agent chain against the real dev stack (task 6.3 AC: ", _render_invoice_image_base64(), _set_common_env(), test_matching_invoice_reaches_approval_queue_with_extracted_fields(), test_reject_path_never_creates_a_draft_entry(), _token()

### Community 111 - "Community 111"
Cohesion: 0.25
Nodes (4): async_sessionmaker, Integration: spend_ledger writes + budget pre-check aggregate against a real Po, _seed_spend(), _sf()

### Community 112 - "Community 112"
Cohesion: 0.25
Nodes (3): _names(), Static validation of the pinned LiteLLM config (task 2.1).  Guards the shape L, test_all_fallback_targets_are_defined_models()

### Community 113 - "Community 113"
Cohesion: 0.29
Nodes (8): approvals.py _RESUMERS registry (generalized dual-agent resume dispatch), Rationale: deterministic branch_suffix collision on repeated runs, agents/dev_agent/graph.py (dedicated LangGraph), servers/github.py (read_repo, create_branch, open_pr, commit_file), servers/jira.py (jira.search, jira.get_issue), fleet-mcp workspace package (6 servers), servers/slack.py (slack.post), Rationale: GitHub 422 no-commits-between-branches on open_pr

### Community 114 - "Community 114"
Cohesion: 0.32
Nodes (7): Permission, permissions_for(), Role-based access control: roles, permissions, and the enforcement dependency., Union of permissions granted by the user's roles., Dependency factory: allow the request only if the user holds `perm`., require_permission(), StrEnum

### Community 115 - "Community 115"
Cohesion: 0.25
Nodes (8): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, Fleet AI Operations Platform, Problem Statement, Fleet Vision (single internal platform), Platform-Level Success Metrics, Why This Approach Wins

### Community 116 - "Community 116"
Cohesion: 0.39
Nodes (8): CI job: build-image (docker build + trivy scan), CI job: integration (pytest tests/integration, testcontainers), CI job: lint (ruff + mypy), CI job: security (bandit + gitleaks), CI job: unit (pytest tests/unit), CI GitHub Actions workflow, gitleaks/gitleaks-action@v2, Trivy scan via aquasec/trivy docker image (not trivy-action)

### Community 117 - "Community 117"
Cohesion: 0.43
Nodes (5): _FakeWebhookSender, fleet_mcp.servers.slack: slack.post via webhook (task 5.3, dept scenario 03)., test_contract_declares_write_internal(), test_post_to_allowlisted_channel_dispatches(), test_post_to_non_allowlisted_channel_is_refused()

### Community 118 - "Community 118"
Cohesion: 0.36
Nodes (6): core.langfuse_client: push a feedback score onto a Langfuse trace (task 4.3, TRD, _RecordingTransport, test_push_score_body_carries_trace_id_and_value(), test_push_score_posts_to_scores_endpoint_with_basic_auth(), test_push_score_raises_on_http_error(), test_push_score_without_reason_omits_comment()

### Community 119 - "n8n Queue Mode + SSO Proxy"
Cohesion: 0.38
Nodes (7): PROGRESS 6.1 n8n queue mode + SSO proxy + Fleet API key service, n8n-main service (queue mode editor/API), n8n-oauth2-proxy service (Keycloak SSO gate), n8n-worker service (Bull/Redis queue consumer), n8n queue mode rationale (TRD §3/§15), n8n SSO proxy rationale (fair-code license forbids embedding), oidc-audience-mapper protocol mapper fix (Keycloak 26 omits aud)

### Community 120 - "Community 120"
Cohesion: 0.29
Nodes (7): Keycloak (OIDC), Web UI (Next.js/TS), Next.js 15 Frontend, AuthN/AuthZ (Keycloak OIDC + RBAC), RBAC Role Matrix, End-User Screens, E2E Tests (Playwright)

### Community 121 - "Community 121"
Cohesion: 0.29
Nodes (7): Microsoft Presidio + TR Recognizers, Embedding Dedup (content_sha256), Loki Structured Logs, Data Classification (sensitivity levels), PII Pipeline (Presidio + TR recognizers), Redaction Downgrade Rule, chunks Table

### Community 122 - "Community 122"
Cohesion: 0.29
Nodes (6): name, packageManager, private, scripts, build, lint

### Community 123 - "Community 123"
Cohesion: 0.38
Nodes (3): _FakeResult, _FakeSession, Any

### Community 125 - "Community 125"
Cohesion: 0.40
Nodes (6): Definition of Done, Doc/Split Sync Contract, Fleet Platform (CLAUDE.md guidance), Mandatory Skills (superpowers + graphify), PROGRESS.md Durable Memory Protocol, Task Execution Protocol

### Community 126 - "Community 126"
Cohesion: 0.33
Nodes (6): Dev setup bootstrap (task 10.1), Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four environments (local/test/demo-staging/prod), Shared Helm chart (per-env values), README.md — fleet-workflow

### Community 127 - "Community 127"
Cohesion: 0.33
Nodes (6): Agent Hub, Control Plane (guardrails, HITL, eval, audit), Fleet — AI Operations Platform (Overview), Knowledge Base (RAG), Support Copilot (Customer Service agent), Workflow Studio (n8n)

### Community 128 - "Community 128"
Cohesion: 0.47
Nodes (6): Budget Hierarchy (global→dept→agent→user), Cost & Token Optimization (§5), Data Model (PostgreSQL core tables, §11), Prompt Caching, Semantic Cache, Spend Ledger

### Community 129 - "Community 129"
Cohesion: 0.40
Nodes (6): 2.2 Model Registry, Sprint 6 — n8n Automations, 6.1 n8n Queue Mode + API Keys, 6.2 Automation #1 — Weekly Summary, 7.1 Admin: Users, Models, Budgets, API Keys, Insights Publisher (Marketing)

### Community 130 - "Community 130"
Cohesion: 0.40
Nodes (6): Gateway-Everything Principle, LLM Gateway (LiteLLM Proxy), MCP Servers, Observability Stack (Langfuse/Prometheus/Grafana/Loki), Model Registry, Agent Builder Screen

### Community 131 - "Community 131"
Cohesion: 0.33
Nodes (6): Secure and Observable by Default, Langfuse (self-hosted), Trace ID Correlation, Langfuse LLM Layer (traces/generations), Output Guards (RAG grounding check), Evaluation (golden sets)

### Community 132 - "Community 132"
Cohesion: 0.47
Nodes (6): LiteLLM Proxy, Ollama (dev local models), vLLM (prod GPU), Fallback Chains & Circuit Breaking, Local-Model Lane (pii/confidential), Reference Sizing

### Community 133 - "Eval Threshold Config"
Cohesion: 0.33
Nodes (6): TRD §13.4 Per-agent eval threshold policy, evals/config.yaml (per-agent thresholds), invoice_agent eval config entry (threshold 0.90), Nightly GitHub Actions Workflow, Nightly e2e Job, Nightly eval Job

### Community 134 - "Community 134"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 135 - "Community 135"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat endpoint's Analytics reply path against the real dev stack (t, test_analytics_reply_shows_sql_for_a_business_question()

### Community 136 - "Community 136"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat SSE + feedback against the real dev stack (task 4.3 AC: "stre, test_chat_stream_renders_answer_and_feedback_lands_in_langfuse()

### Community 137 - "Community 137"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: `/v1/rag/query` end to end against the real dev-stack (task 3.3 AC, test_rag_query_returns_grounded_answer_with_citations()

### Community 138 - "Fleet API Key Service"
Cohesion: 0.40
Nodes (5): apps/api/fleet_api/routers/api_keys_admin.py, apps/api/fleet_api/api_keys.py (pure hash/validate), Fleet-issued API-key service-auth layer, migration 0008_api_keys (api_keys table), platform_admin/dept_admin vs seeded-realm role-string gap (recurring, now 5+ admin routers)

### Community 139 - "Community 139"
Cohesion: 0.50
Nodes (3): Any, Protocol, ReasoningUtilityClient

### Community 141 - "Community 141"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 142 - "Community 142"
Cohesion: 0.40
Nodes (4): JWT, next-auth, next-auth/jwt, Session

### Community 143 - "Community 143"
Cohesion: 0.70
Nodes (5): Sprint 3 Report — RAG (Ingestion, Collections, Query, Web Shell), Sprint 3 Task 3.1 Ingestion pipeline, Sprint 3 Task 3.2 Collections + retention, Sprint 3 Task 3.3 Query + citations, Sprint 3 Task 3.4 Web shell + Knowledge UI

### Community 144 - "Community 144"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 145 - "Community 145"
Cohesion: 0.40
Nodes (5): Security Testing (trivy/bandit/semgrep/ZAP/garak), Prometheus/Grafana Metrics, Prompt Injection Defense (quarantine blocks), Security Tests (garak/injection corpus), Risks & Mitigations

### Community 146 - "Community 146"
Cohesion: 0.40
Nodes (5): Default Model Matrix, Routing & Tiering (utility/reasoning), Model Tiering (utility vs reasoning), Prompt Caching, agents Table

### Community 147 - "Community 147"
Cohesion: 0.60
Nodes (4): Alembic environment. Uses a sync psycopg2 URL derived from FLEET_DATABASE_URL., run_migrations_offline(), run_migrations_online(), _sync_url()

### Community 148 - "Community 148"
Cohesion: 0.50
Nodes (3): _builder_token(), Integration: `/v1/admin/agents` CRUD + pause/resume against the real dev stack, test_agent_crud_and_pause_blocks_a_real_graph_run()

### Community 155 - "Community 155"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 156 - "Community 156"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

### Community 166 - "Community 166"
Cohesion: 1.00
Nodes (3): openapi.json (dumped API schema), packages/shared README — @fleet/shared, src/schema.d.ts (generated, do not hand-edit)

## Ambiguous Edges - Review These
- `Self-Service Analytics Agent (Text-to-SQL)` → `Qdrant Vector DB`  [AMBIGUOUS]
  docs/source/PROJECT_OVERVIEW.md · relation: conceptually_related_to

## Knowledge Gaps
- **257 isolated node(s):** `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)`, `Listing Quality Agent (Listings Ops)`, `Insights Publisher Agent (Marketing)`, `Agent Hub` (+252 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **69 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Self-Service Analytics Agent (Text-to-SQL)` and `Qdrant Vector DB`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `fleet_api/registry.py — model registry` connect `Community 1` to `Community 26`, `Community 14`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `run_ingestion()` connect `Community 3` to `Community 2`, `Community 10`, `Community 12`, `Community 39`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `PgReadOnlyTool` connect `Community 9` to `Community 65`, `Community 68`, `Community 69`, `Community 38`, `Community 7`, `Community 40`, `Community 11`, `Community 46`, `Community 23`, `Community 25`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `KillSwitch` (e.g. with `AgentIn` and `AgentOut`) actually correct?**
  _`KillSwitch` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `SlackPostTool` (e.g. with `ApprovalOut` and `DecisionIn`) actually correct?**
  _`SlackPostTool` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `GitHubTool` (e.g. with `ApprovalOut` and `DecisionIn`) actually correct?**
  _`GitHubTool` has 31 INFERRED edges - model-reasoned connections that need verification._
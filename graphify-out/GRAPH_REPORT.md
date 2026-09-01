# Graph Report - .  (2026-09-01)

## Corpus Check
- 151 files · ~218,280 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3832 nodes · 6913 edges · 331 communities (240 shown, 91 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 1341 edges (avg confidence: 0.69)
- Token cost: 243,862 input · 76,978 output

## Community Hubs (Navigation)
- Citations & Grounding
- Examples Gallery
- Web App Pages
- API Key Auth
- Object & Vector Stores
- Chunking Pipeline
- Model Registry & Probes
- Structured Logging & PII Scrub
- LLM Gateway Client
- Chat Data Model
- Project Vision Docs
- MCP Server Base
- Auth & DB Models
- PII Detection Policy
- n8n Client
- GitHub Tool Backend
- Budget Enforcement
- Semantic Cache
- HR CV Extraction
- Sprint 6 Report
- OCR Sensitivity Routing
- RBAC & Collections
- Technical Requirements
- Kill Switches
- Admin Screens
- TypeScript Config
- Gateway Client Tests
- Approval Resume Adapters
- Analytics Agent Service
- Engineering Findings Log
- Automation Service Surface
- Eval Runner
- Erasure & PII Lane Tests
- NL-to-SQL Generation
- Dev Agent Guardrails
- Sensitivity Routing
- Department Scenarios
- Langfuse Redaction
- Project Overview
- Pricing Sync
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
- Community 192
- Community 193
- Community 194
- Community 195
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
- Community 258
- Community 259
- Community 260
- Community 261
- Community 262
- Community 263
- Community 264
- Community 265
- Community 266
- Community 267
- Community 268
- Community 269
- Community 272
- Community 273
- Community 274
- Community 275
- Community 276
- Community 277
- Community 278
- Community 279
- Community 280
- Community 281
- Community 282
- Community 283
- Community 284
- Community 285
- Community 286
- Community 287
- Community 288
- Community 289
- Community 290
- Community 291
- Community 293
- Community 298
- Community 299
- Community 307
- Community 308
- Community 309
- Community 310
- Community 311
- Community 312
- Community 313
- Community 314
- Community 315
- Community 316
- Community 317
- Community 318
- Community 319
- Community 320
- Community 321
- Community 322
- Community 323
- Community 324
- Community 325
- Community 326
- Community 327
- Community 328

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 73 edges
2. `KillSwitch` - 51 edges
3. `Settings` - 49 edges
4. `LLMClient` - 44 edges
5. `Agent` - 40 edges
6. `ToolContract` - 35 edges
7. `Hit` - 30 edges
8. `SlackPostTool` - 28 edges
9. `Permission` - 27 edges
10. `FakeTransport` - 27 edges

## Surprising Connections (you probably didn't know these)
- `test_seed_populates_and_creates_views()` --calls--> `seed()`  [INFERRED]
  tests/integration/test_seed_runs.py → apps/api/fleet_api/seed.py
- `test_load_dataset_parses_jsonl_into_cases()` --calls--> `load_dataset()`  [INFERRED]
  tests/unit/test_eval_runner.py → evals/runner.py
- `test_case_result_is_a_dataclass_with_id_and_reason()` --calls--> `CaseResult`  [INFERRED]
  tests/unit/test_eval_runner.py → evals/runner.py
- `test_load_analytics_dataset_parses_jsonl()` --calls--> `load_analytics_dataset()`  [INFERRED]
  tests/unit/test_eval_runner_analytics.py → evals/runner.py
- `test_load_dev_agent_dataset_parses_jsonl()` --calls--> `load_dev_agent_dataset()`  [INFERRED]
  tests/unit/test_eval_runner_dev_agent.py → evals/runner.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **KVKK Local-Lane Enforcement Chain** — docs_technical_requirements_data_classification, docs_technical_requirements_sensitivity_clearance, docs_technical_requirements_sensitivity_routing, docs_technical_requirements_redaction_downgrade, docs_technical_requirements_local_model_lane, docs_reports_sprint_8_ocr_sensitivity_gating, docs_reports_sprint_8_no_cloud_egress_proof [EXTRACTED 1.00]
- **write:external HITL Approval Flow** — docs_technical_requirements_risk_class, docs_technical_requirements_approval_queue, docs_technical_requirements_langgraph_runtime, docs_technical_requirements_kill_switches, docs_progress_approval_resumer_registry, docs_reports_sprint_8_checkpointer_setup_gap [EXTRACTED 1.00]
- **Post-MVP Wave 1-2 Scenario Onboarding** — docs_department_scenarios_onboarding_checklist, docs_split_implementation_plan_sprint_11_wave_1_scenarios_listing_quality_agent, docs_split_implementation_plan_sprint_11_wave_1_scenarios_vehicle_intake_agent, docs_split_implementation_plan_sprint_11_wave_1_scenarios_insights_publisher_agent, docs_split_implementation_plan_sprint_12_wave_2_scenarios_dealer_onboarding_agent, docs_split_implementation_plan_sprint_12_wave_2_scenarios_legal_review_agent, docs_technical_requirements_eval_gate [EXTRACTED 1.00]
- **Fleet Observability Pipeline (scrape -> alert -> route -> visualize)** — infra_compose_prometheus_prometheus_scrape_config, infra_compose_prometheus_alerts_fleet_platform_group, infra_compose_alertmanager_alertmanager_slack_receiver, infra_compose_grafana_provisioning_datasources_datasources_prometheus_ds, infra_compose_grafana_provisioning_datasources_datasources_loki_ds [INFERRED 0.85]
- **KVKK Local PII Lane (no cloud model cleared for pii)** — gateway_litellm_config_sensitivity_clearance, gateway_litellm_config_local_lane, gateway_litellm_config_local_reasoning, gateway_litellm_config_local_embeddings, gateway_litellm_config_fallback_chains [EXTRACTED 1.00]
- **SSO-Gated n8n Queue Automation Surface** — infra_compose_docker_compose_dev_n8n_main, infra_compose_docker_compose_dev_n8n_worker, infra_compose_docker_compose_dev_n8n_oauth2_proxy, infra_compose_docker_compose_dev_keycloak, infra_compose_docker_compose_dev_redis_db_partitioning [EXTRACTED 1.00]
- **Sprint 3 RAG pipeline stages: ingestion, collections, query/citations, web shell** — docs_reports_sprint_3_md_task_3_1, docs_reports_sprint_3_md_task_3_2, docs_reports_sprint_3_md_task_3_3, docs_reports_sprint_3_md_task_3_4 [EXTRACTED 1.00]
- **Gateway client call orchestration: routing -> transport -> ledger/cost -> budget** — apps_runtime_core_llm_client, apps_runtime_core_llm_routing, apps_runtime_core_llm_transport, apps_runtime_core_llm_ledger, fleet_api_budget [EXTRACTED 0.90]
- **KVKK Sensitivity Routing & Redaction Flow** — docs_source_technical_requirements_pii_pipeline, docs_source_technical_requirements_redaction_downgrade, docs_source_technical_requirements_sensitivity_routing, docs_source_technical_requirements_local_model_lane [EXTRACTED 0.90]
- **LLM Gateway Cost Governance (registry, budgets, spend ledger)** — docs_source_technical_requirements_llm_gateway, docs_source_technical_requirements_model_registry, docs_source_technical_requirements_budget_hierarchy, docs_source_technical_requirements_spend_ledger [EXTRACTED 0.85]
- **Guardrails + HITL External-Write Control** — docs_source_technical_requirements_guardrails_hitl, docs_source_technical_requirements_tool_risk_class, docs_source_technical_requirements_approval_queue, docs_source_technical_requirements_langgraph_runtime [EXTRACTED 0.85]
- **Sprint 1 three-stage delivery (foundation, CI, auth/middleware/helm)** — docs_superpowers_plans_2026_07_15_sprint_1_stage_a_plan, docs_superpowers_plans_2026_07_15_sprint_1_stage_b_plan, docs_superpowers_plans_2026_07_16_sprint_1_stage_c_plan [EXTRACTED 1.00]
- **CI Pipeline: lint -> unit -> {integration, security, build-image}** — github_workflows_ci_job_lint, github_workflows_ci_job_unit, github_workflows_ci_job_integration, github_workflows_ci_job_security, github_workflows_ci_job_build_image [INFERRED 0.85]
- **Fleet k3d/Helm Service Stack (8 templated services)** — infra_helm_fleet_templates_postgres_postgres, infra_helm_fleet_templates_redis_redis, infra_helm_fleet_templates_qdrant_qdrant, infra_helm_fleet_templates_minio_minio, infra_helm_fleet_templates_keycloak_keycloak, infra_helm_fleet_templates_prometheus_prometheus [INFERRED 0.75]
- **Fleet Five Core Modules** — docs_project_overview_agent_hub, docs_project_overview_workflow_studio, docs_project_overview_knowledge_base_rag, docs_project_overview_integration_layer_mcp, docs_project_overview_control_plane [EXTRACTED 1.00]
- **Cost Governance Stack** — docs_split_technical_requirements_05_cost_token_optimization_budget_hierarchy, docs_split_technical_requirements_05_cost_token_optimization_spend_ledger, docs_split_technical_requirements_05_cost_token_optimization_cost_anomaly_alerts, docs_split_technical_requirements_03_tech_stack_litellm [EXTRACTED 0.85]
- **Guardrails & HITL Approval Flow** — docs_split_technical_requirements_09_guardrails_hitl_tool_risk_class, docs_split_technical_requirements_09_guardrails_hitl_approval_queue, docs_split_technical_requirements_03_tech_stack_langgraph, docs_split_technical_requirements_11_data_model_core_tables [EXTRACTED 0.85]

## Communities (331 total, 91 thin omitted)

### Community 0 - "Citations & Grounding"
Cohesion: 0.05
Nodes (67): Answer, build_answer(), Citation, Generator, Protocol, Grounded answer + citation guardrail (task 3.3, TRD §9 structural check).  Eve, Return citations if every 1-indexed position resolves to a retrieved hit., _resolve_citations() (+59 more)

### Community 1 - "Examples Gallery"
Cohesion: 0.06
Nodes (43): EvalCase, Examples-gallery case (task 6.5.2, TRD §11 deferred eval_datasets shape)., create_example(), ExampleIn, ExampleOut, list_examples(), Any, AsyncSession (+35 more)

### Community 2 - "Web App Pages"
Cohesion: 0.07
Nodes (37): ApprovalsPage(), ChatPage(), KnowledgePage(), ApprovalOut, ApprovalsQueue(), AgentSummary, ChatMessage, ChatWindow() (+29 more)

### Community 3 - "API Key Auth"
Cohesion: 0.07
Nodes (54): ApiKeyInvalid, ApiKeyRecord, generate_key(), has_scope(), hash_key(), keys_match(), datetime, Exception (+46 more)

### Community 4 - "Object & Vector Stores"
Cohesion: 0.05
Nodes (44): ensure_bucket(), minio_client_from_env(), object_key(), Minio, MinIO object store for uploaded documents (TRD §3 tech stack, task 3.1).  Obje, sha256_bytes(), collection_name(), delete_by_document() (+36 more)

### Community 5 - "Chunking Pipeline"
Cohesion: 0.08
Nodes (36): Chunk, chunk_text(), dedup_chunks(), Structure-aware chunking + content-hash dedup (TRD Sprint 3 task 3.1).  Splits, Pack paragraphs into chunks of at most `max_tokens` words each., Drop chunks whose content hash is already embedded (0 new-embedding re-upload)., _sha256(), EmbeddingClient (+28 more)

### Community 6 - "Model Registry & Probes"
Cohesion: 0.07
Nodes (39): build_model_row(), evaluate_smoke(), _is_local(), ModelDraft, probe_model(), Connectivity/capability smoke probe for the model registry (task 2.2).  Runs a, Send a 1-token completion to `draft.litellm_model_id` via the proxy.      Reac, Any (+31 more)

### Community 7 - "Structured Logging & PII Scrub"
Cohesion: 0.07
Nodes (36): get_logger(), _JsonFormatter, LokiPushHandler, PiiScrubFilter, Logger, Request, Structured JSON logging with PII scrubbing (CLAUDE.md conventions: "structured J, Structured JSON logger: stdout always, Loki push best-effort (set     FLEET_LOKI (+28 more)

### Community 8 - "LLM Gateway Client"
Cohesion: 0.11
Nodes (25): BudgetChecker, EmbeddingResponse, _first_content(), GatewayError, Ledger, LLMResponse, _opt_float(), Any (+17 more)

### Community 9 - "Chat Data Model"
Cohesion: 0.13
Nodes (37): Agent, Conversation, Feedback, Message, Governed agent config (TRD §11, §4.2 tiering, §5 semantic cache, §9 kill switch), A chat thread with an agent (TRD §11)., A single turn in a conversation (TRD §11 — carries cost + citations)., Thumbs up/down on a message (TRD §11, §4.3 Chat UI AC). (+29 more)

### Community 10 - "Project Vision Docs"
Cohesion: 0.05
Nodes (37): 1. Vision, 2. Problem Statement, 3.1 Agent Hub, 3.2 Workflow Studio (n8n), 3.3 Knowledge Base (RAG), 3.4 Integration Layer (MCP), 3.5 Control Plane, 3. Solution: The Fleet Platform (+29 more)

### Community 11 - "MCP Server Base"
Cohesion: 0.09
Nodes (21): MCPAuthError, MCPServer, Any, MCP server base: tool registry with declared risk_class, schema validation, and, Raised when a call_tool request carries a wrong/missing API key., Registry + dispatcher for one MCP server's tools., _validate_schema(), erp MCP tool: create_draft_entry (task 6.3, dept scenario 04 Invoice & Reconcil (+13 more)

### Community 12 - "Auth & DB Models"
Cohesion: 0.13
Nodes (33): get_current_user(), AsyncSession, Verify the bearer token, then resolve permissions against the DB     `roles` ta, Base, Chunk, Department, PromptVersion, SQLAlchemy declarative models for the first migration (users, departments, roles (+25 more)

### Community 13 - "PII Detection Policy"
Cohesion: 0.09
Nodes (30): AnalyzerEngine, _analyzer(), apply_pii_policy(), PiiFinding, PiiPolicyError, PolicyResult, Any, ValueError (+22 more)

### Community 14 - "n8n Client"
Cohesion: 0.15
Nodes (23): N8nClient, Any, activate_workflow(), ActiveIn, _catalog_entry(), deactivate_workflow(), _find_workflow(), _get_meta() (+15 more)

### Community 15 - "GitHub Tool Backend"
Cohesion: 0.11
Nodes (16): BranchNamePatternError, build_default_backend(), GitHubBackend, GitHubTool, Any, Exception, Protocol, github MCP tool: read_repo/create_branch/open_pr (task 5.3, dept scenario 03 De (+8 more)

### Community 16 - "Budget Enforcement"
Cohesion: 0.10
Nodes (27): BudgetExceeded, BudgetStatus, check_budget(), DbBudgetChecker, evaluate_budget(), _period_start(), Any, async_sessionmaker (+19 more)

### Community 17 - "Semantic Cache"
Cohesion: 0.12
Nodes (15): CacheHit, _cosine(), Protocol, Redis-backed semantic cache (TRD §5).  Opt-in per agent (deterministic Q&A age, RedisLike, SemanticCache, _FakeRedis, core.semantic_cache: Redis-backed semantic cache (task 4.2, TRD §5).  Opt-in p (+7 more)

### Community 18 - "HR CV Extraction"
Cohesion: 0.11
Nodes (27): extract_cv_profile(), _normalize_phone(), Any, Protocol, CV text -> structured profile (task 8.1/8.2, dept scenario 05 "CV -> structured, ReasoningClient, _strip_code_fence(), _FakeLLM (+19 more)

### Community 19 - "Sprint 6 Report"
Cohesion: 0.09
Nodes (31): Cross-cutting rules honored, Deviations / deferrals, Notable issues resolved (symptom → root cause → fix), Sprint 6 Report — n8n Automations, Tasks & Acceptance Criteria, What was tested and how, Alertmanager Slack Receiver (#fleet-alerts), __SLACK_WEBHOOK_URL__ Startup Substitution (+23 more)

### Community 20 - "OCR Sensitivity Routing"
Cohesion: 0.12
Nodes (25): ocr_image(), OcrResult, Any, Protocol, OCR step: vision-LLM primary, tesseract fallback (TRD §3 tech stack, task 3.1);, Run vision-LLM OCR (skipped for confidential/pii); fall back to (or, for     co, _try_vision(), VisionClient (+17 more)

### Community 21 - "RBAC & Collections"
Cohesion: 0.15
Nodes (27): Collection, RAG document collection (TRD §8 data classification, §11)., Permission, permissions_for(), Role-based access control: roles, permissions, and the enforcement dependency., Union of permissions granted by the user's roles., Dependency factory: allow the request only if the user holds `perm`., require_permission() (+19 more)

### Community 22 - "Technical Requirements"
Cohesion: 0.07
Nodes (29): 10. Scalability & Capacity, 11. Data Model (PostgreSQL — core tables), 12. Admin & End-User Screens (Functional), 13. Testing Strategy (from the first sprint, CI-gated), 14. Environments, CI/CD, Backup, 15. Phase Map (what ships when), 16. Risks, 1. Goals, Non-Goals, Design Principles (+21 more)

### Community 23 - "Kill Switches"
Cohesion: 0.14
Nodes (19): get_killswitch(), KillSwitch, _pause_key(), Runtime-side enforcement, checked before any graph node runs a step., _Clock, _FakeRedis, datetime, core.killswitch: per-agent pause + global read-only mode (task 4.2, TRD §9). (+11 more)

### Community 24 - "Admin Screens"
Cohesion: 0.15
Nodes (17): AgentOut, ApiKeyOut, ApiKeysAdmin(), AVAILABLE_SCOPES, AuditExplorer(), AuditRowOut, ASSIGNABLE_ROLES, DepartmentOut (+9 more)

### Community 25 - "TypeScript Config"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 26 - "Gateway Client Tests"
Cohesion: 0.19
Nodes (22): _client(), FakeLedger, FakeTransport, Gateway client orchestration (task 2.3).  The client is the ONLY place LLM cal, §6 trace correlation: the proxy's Langfuse callback must tag the trace     with, Records calls; returns a canned OpenAI-style body, or raises to simulate     an, test_embeddings_forwards_trace_id_to_transport(), test_embeddings_pii_routes_to_local_model() (+14 more)

### Community 27 - "Approval Resume Adapters"
Cohesion: 0.11
Nodes (24): _OcrToolAdapter, Any, Same rebuild-fresh-and-resume mechanism as Dev Agent, for Invoice     Agent's e, `build_ocr_tool` returns a bare callable (`image_base64 -> {text, source}`);, Rebuild the Dev Agent graph bound to the approval's run_id (thread_id)     agai, _resume_dev_agent_run(), _resume_hr_agent_run(), _resume_invoice_agent_run() (+16 more)

### Community 28 - "Analytics Agent Service"
Cohesion: 0.13
Nodes (22): AnalyticsClarification, AnalyticsRefusal, AnalyticsResult, ask_analytics(), GovernedQueryTool, Any, Exception, Protocol (+14 more)

### Community 29 - "Engineering Findings Log"
Cohesion: 0.10
Nodes (28): Self-Service Analytics (Data), Sprint 1 — Repo, Stack, CI, Gateway, Markdown Code-Fence Stripping Defense, docker compose --env-file Auto-Discovery Gap, DB-Backed RBAC (roles re-read per request), PROGRESS.md Append-Only Durable Log, Keycloak Realm vs rbac.py Role-String Gap, trace_id Never Forwarded to Langfuse (Sprint 2 defect) (+20 more)

### Community 30 - "Automation Service Surface"
Cohesion: 0.16
Nodes (21): get_pg_ro_tool(), get_slack_tool(), pg_query(), PgQueryIn, PgQueryOut, BaseModel, Service-to-Fleet-API surface for automations (task 6.1/6.2, TRD §7.1).  Routes, slack_post() (+13 more)

### Community 31 - "Eval Runner"
Cohesion: 0.14
Nodes (26): CaseResult, _extract_cv_profile_for_case(), load_analytics_dataset(), load_dataset(), load_dev_agent_dataset(), _load_dotenv_fallback(), load_hr_agent_dataset(), load_invoice_dataset() (+18 more)

### Community 32 - "Erasure & PII Lane Tests"
Cohesion: 0.11
Nodes (17): _admin_token(), Integration: DELETE /v1/subjects/{hash} against the real dev-stack (task 8.3 AC:, test_erase_subject_removes_conversation_document_and_pseudonymizes_audit(), _FakeQdrantSink, llm_client(), _NullLedger, Any, Task 8.2 AC: "integration test proves a pii request never reaches a cloud provid (+9 more)

### Community 33 - "NL-to-SQL Generation"
Cohesion: 0.14
Nodes (22): _build_system_prompt(), ClarificationNeeded, generate_sql(), Any, Exception, Protocol, NL question -> SQL (task 5.2, dept scenario 02 "SQL gen" call-site, TRD §4.3 re, Some models wrap JSON in a ```json ... ``` fence despite being told not     to; (+14 more)

### Community 34 - "Dev Agent Guardrails"
Cohesion: 0.14
Nodes (24): DevAgentState, TypedDict, assert_diff_size_ok(), assert_no_protected_paths(), assert_ticket_labeled(), DiffTooLargeError, ProtectedPathError, Any (+16 more)

### Community 35 - "Sensitivity Routing"
Cohesion: 0.13
Nodes (22): _clearance(), effective_sensitivity(), Any, Exception, Sensitivity routing — the KVKK guardrail (CLAUDE.md rule 2, TRD §4.3 + §8).  P, Ordered classification: public < internal < confidential < pii (§4.2)., Raised when no model's clearance covers the request's effective sensitivity., Return max(inputs), applying the §8 redaction-downgrade rule.      Content tha (+14 more)

### Community 36 - "Department Scenarios"
Cohesion: 0.12
Nodes (26): Dealer Onboarding (Corporate Sales), HR Talent & Onboarding (HR), Invoice & Reconciliation (Finance), Legal Document Review (Legal), Protected-Attribute Schema Exclusion, Vehicle Intake (Trink sat!), 15-Minute Demo Script, Sprint 6 — n8n Automations (+18 more)

### Community 37 - "Langfuse Redaction"
Cohesion: 0.13
Nodes (16): get_langfuse_redactor(), get_langfuse_scorer(), LangfuseRedactor, LangfuseScorer, _now_iso(), AsyncClient, Push a feedback score onto a Langfuse trace (TRD §6, task 4.3 AC: "👍/👎 lands in, score is +1 (thumbs up) or -1 (thumbs down); Langfuse NUMERIC score. (+8 more)

### Community 38 - "Project Overview"
Cohesion: 0.08
Nodes (24): 1. Vision, 2. Problem Statement, 3.1 Agent Hub, 3.2 Workflow Studio (n8n), 3.3 Knowledge Base (RAG), 3.4 Integration Layer (MCP), 3.5 Control Plane, 3. Solution: The Fleet Platform (+16 more)

### Community 39 - "Pricing Sync"
Cohesion: 0.14
Nodes (22): _is_local(), _load_litellm_price_map(), main(), PriceValidationError, Any, Exception, Pricing sync for the LiteLLM proxy config (task 2.1).  Keeps the per-token inp, Best-effort load of LiteLLM's canonical price map; empty if unavailable. (+14 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (20): Async database engine, session factory, and URL resolution for the Fleet API., Approval, HITL approval-queue entry for a write:external tool call (TRD §9, §11)., ApprovalOut, decide_approval(), DecisionIn, list_approvals(), AsyncSession (+12 more)

### Community 41 - "Community 41"
Cohesion: 0.17
Nodes (23): database_url(), get_engine(), Return the async database URL from FLEET_DATABASE_URL, or the local default., Create an async engine for the given URL (defaults to database_url())., main(), Seed synthetic data and analytics fixture warehouse views. Idempotent., Support Copilot demo agent + its cs-help-center/cs-procedures collections     (, Analytics demo agent (task 5.2, department scenario 02). No RAG     collections (+15 more)

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (24): Dev Agent (IT/Engineering), Insights Publisher (Marketing), Rollout Ladder: assist → supervised → autonomous, Support Copilot (Customer Service), Sprint 4 — Agent Runtime, Chat, First Agent, Sprint 5 — MCP, Agents #2-3, Approvals, Per-Agent Approval Resumer Registry, KillSwitch bytes-vs-str Redis Bug (+16 more)

### Community 43 - "Community 43"
Cohesion: 0.11
Nodes (20): Deferrable Tasks, Demo Script (15 min), Fleet — Implementation Plan (Sprint Backlog), Sprint 0 — Prerequisites (user-assisted), Sprint 10 — Demo Assembly & Docs, Sprint 2 — LLM Gateway, Model Registry, Budgets, Sprint 3 — RAG, Sprint 4 — Agent Runtime, Chat, First Agent (+12 more)

### Community 44 - "Community 44"
Cohesion: 0.18
Nodes (23): evaluate_invoice_case(), InvoiceAnswer, InvoiceCase, Word-for-word fuzzy match, tolerant of OCR-level diacritic noise (ı/i,     ş/s,, One synthetic invoice (task 6.3, dept scenario 04 evals: field     extraction a, _vendor_reasonably_matches(), _case(), evals.runner: Invoice Agent eval assertion checking (task 6.3, dept scenario 04 (+15 more)

### Community 45 - "Community 45"
Cohesion: 0.17
Nodes (18): CurrentUser, The authenticated principal extracted from a verified token., _build_app(), FastAPI, fleet_api.routers.budgets_admin: budgets CRUD (task 7.1b, TRD §5). Only the RBA, test_global_scope_with_scope_id_rejected_before_touching_db(), test_member_cannot_list_budgets(), test_non_global_scope_without_scope_id_rejected_before_touching_db() (+10 more)

### Community 46 - "Community 46"
Cohesion: 0.17
Nodes (17): list_tickets(), AsyncSession, BaseModel, Dev Agent run trigger (task 5.5, dept scenario 03).  `POST /v1/dev-agent/runs`, Fixture tickets for a run-dialog picker (task 6.5.3, examples gallery     try-i, RunIn, RunOut, start_run() (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (18): DevAgentPlan, plan_ticket(), PlanParseError, Any, Exception, Protocol, Ticket -> plan (task 5.5, dept scenario 03 "plan" step, TRD §4.3 reasoning tier, The model's plan response was malformed or missing a required field. (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.23
Nodes (19): build_graph(), Compile the base graph for one agent, bound to a checkpointer for resume., _FakeLLMClient, _FakeRedis, _noop_tool(), Runtime base graph (task 4.1). AC: unit with FakeLLM — routing utility-vs- reas, A write:internal tool with autonomy already granted reaches execute_tool     di, Read-only can be flipped on by an admin while a HITL approval is     pending; t (+11 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (22): INTEGRATION-POINT Mock Marker, Listing Quality (Listings Ops), Generic Department Onboarding Checklist, Department Wave Plan (10 Scenarios), Sprint 0 — User-Assisted Prerequisites, Fleet Implementation Plan (Sprint Backlog), Windows ProactorEventLoop / psycopg Incompatibility, n8n CLI Activation Needs a Restart (+14 more)

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (17): AsyncEngine, Append-only audit log writes., Insert one append-only audit row. Never updates or deletes., write_audit(), get_settings(), Application settings, loaded from the environment (pydantic-settings)., Return a fresh Settings instance (call at app creation, not import time)., Prometheus HTTP metrics for the API layer (task 7.4, TRD §6/§13.5).  Labeled b (+9 more)

### Community 51 - "Community 51"
Cohesion: 0.22
Nodes (15): N8nResult, Thin async client over the n8n REST + webhook surfaces (task 6.5.3).  Reached, _build_app(), _FakeN8nClient, FastAPI, fleet_api.routers.workflows: friendly n8n catalog + run/activate proxy (task 6., Overrides get_current_user (not require_permission's per-call-site     closures, test_builder_can_activate_workflow() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (13): build_default_backend(), FixtureJiraBackend, IssueNotFoundError, JiraBackend, Any, Exception, Protocol, jira MCP tool: search/get_issue (task 5.3, dept scenario 03 Dev Agent).  # INT (+5 more)

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (18): _extension(), _extract_docx(), _extract_pdf(), extract_text(), _extract_txt(), ExtractResult, ValueError, Text extraction from uploaded documents (task 3.1: extract step).  Dispatches (+10 more)

### Community 54 - "Community 54"
Cohesion: 0.18
Nodes (12): EvalCase, _build_app(), _FakeResult, _FakeSession, FastAPI, fleet_api.routers.examples: examples gallery CRUD (task 6.5.2). A fake in-memor, Overrides get_current_user (not require_permission's per-call-site     closures, test_create_example_persists_with_user_source() (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.19
Nodes (20): AgentIn, AgentOut, create_agent(), delete_agent(), get_agent(), get_global_read_only(), list_agents(), pause_agent() (+12 more)

### Community 56 - "Community 56"
Cohesion: 0.17
Nodes (13): EmailSender, EmailSendTool, InvalidRecipientError, Exception, Protocol, email MCP tool: SMTP sandbox send (task 5.1).  Always write:external (TRD §9 n, Recipient address is malformed or outside the allowed domain set., _FakeSender (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.19
Nodes (16): extract_invoice_fields(), ExtractionParseError, Any, Exception, Invoice text -> structured fields (task 6.3, dept scenario 04 "extracted fields, The model's field-extraction response was malformed or missing a field., _strip_code_fence(), _FakeLLM (+8 more)

### Community 58 - "Community 58"
Cohesion: 0.10
Nodes (21): 10. Başarı Metrikleri (Platform Seviyesi), 11. Anahtar Mesajlar (Sunum Kapanışı İçin), 1. Proje Nedir?, 2. Şu An Ne Çalışıyor? (6 Sprint Sonunda), 3. Tamamlanan Sprintler (1–6), 5. Planlanan 15 Dakikalık Demo Senaryosu, 6. Teknoloji Seçimleri ve Gerekçeleri, 7. Yönetişim: "Neden Güvenle Kullanılabilir?" (+13 more)

### Community 59 - "Community 59"
Cohesion: 0.20
Nodes (20): _evaluate_hr_extraction_case(), _evaluate_hr_schema_exclusion_case(), _fold(), HrAgentCase, Any, Case-fold for substring matching, Turkish-safe: plain str.lower() turns     'İ', One row of evals/datasets/hr_agent.jsonl (task 8.5, dept scenario 05).     `cas, _tr_ascii_fold() (+12 more)

### Community 60 - "Community 60"
Cohesion: 0.21
Nodes (14): _FakeErp, _FakeLLM, _FakeOcr, _matching_po_lookup(), Any, agents.invoice_agent.graph: image -> OCR -> extract -> validate -> HITL -> draf, Dept scenario 04: mismatch must flag, never auto-draft as clean — but     a mis, Dept scenario 04's "duplicate invoice fixture -> flag" — proven across     two (+6 more)

### Community 61 - "Community 61"
Cohesion: 0.12
Nodes (19): CLAUDE.md — Fleet Platform, Commands, Conventions (condensed), Current Focus, Definition of Done, Doc/Split Sync Contract, Fleet Platform (CLAUDE.md guidance), Rule 1: LLM calls only via gateway client (+11 more)

### Community 62 - "Community 62"
Cohesion: 0.12
Nodes (20): Fleet Helm Umbrella Chart, Grafana Service (Helm), Keycloak Service (Helm), Loki Service (Helm), MinIO Service (Helm), Helm Install NOTES, Postgres Service (Helm), Prometheus Service (Helm) (+12 more)

### Community 63 - "Community 63"
Cohesion: 0.12
Nodes (18): Analytics Agent (#2), Approval Queue (HITL), apps/api/fleet_api/routers/approvals.py, Rationale: deterministic branch_suffix collision on repeated runs, Dev Agent (#3), agents/dev_agent/graph.py (dedicated LangGraph), Cross-cutting rules honored, Deviations / deferrals (+10 more)

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (14): UnauthorizedError, get_current_service_key(), _lookup(), AsyncSession, FastAPI dependency for Fleet-issued API-key auth (task 6.1, TRD §7.1).  Parall, Validate the `X-Fleet-Api-Key` header, or raise 401., Dependency factory: allow the request only if the key holds `scope`., Dependency factory: allow the request if EITHER a Keycloak bearer     token car (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.23
Nodes (16): NonAllowlistedTableError, Query references a table outside the server's allowlist., Query is not a plain read (DML/DDL, or otherwise unsafe)., UnsafeSqlError, _FakeRunner, fleet_mcp.servers.pg_ro: read-only governed-SQL tool (task 5.1, dept scenario 0, test_allowlisted_query_runs_and_returns_rows(), test_auto_limit_appended_when_missing() (+8 more)

### Community 66 - "Community 66"
Cohesion: 0.26
Nodes (15): build_dev_agent_graph(), ReasoningClient, _FakeLLM, _FakeSlackSender, _labeled_ticket(), agents.dev_agent.graph: ticket -> plan -> branch -> PR -> Slack, with a single, Caught before shipping: a raised slack.post() (e.g. an unset/invalid     webhoo, test_approve_resumes_and_opens_pr_and_notifies_slack() (+7 more)

### Community 67 - "Community 67"
Cohesion: 0.21
Nodes (14): build_hr_agent_graph(), KillSwitch, _FakeLLM, _FakeOcr, Any, agents.hr_agent.graph: image -> OCR -> extract profile -> match role -> HITL sho, dept scenario 05: pii lane, reasoning stays local for CV content —     reasserte, A candidate missing most criteria still routes to the SAME approval     queue, n (+6 more)

### Community 68 - "Community 68"
Cohesion: 0.19
Nodes (12): AdminLayout(), AutomationsPage(), Home(), AppShell(), InvoiceUploadDialog(), WorkflowCard(), WorkflowOut, useToast() (+4 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (13): create_app(), FastAPI, FastAPI application factory., Build and configure the Fleet API application.      Set with_middleware=False, main(), Dump the FastAPI OpenAPI schema to a file for TS client generation., Integration test: an audit row is written with the request trace_id, and the ra, test_audit_row_has_trace_id() (+5 more)

### Community 70 - "Community 70"
Cohesion: 0.25
Nodes (17): Environment-driven configuration for the Fleet API., Settings, AuditLog, Per-call LLM spend record (TRD §5 spend ledger, §11). Append-only., SpendLedger, AuditRowOut, BurnDownPoint, cost_summary() (+9 more)

### Community 71 - "Community 71"
Cohesion: 0.19
Nodes (14): _existing_hashes(), ingest_document(), Any, async_sessionmaker, _QdrantSinkAdapter, arq worker: the `ingest_document` task and process entrypoint (task 3.1).  Wir, arq task: fetch the uploaded object, run the ingestion pipeline, persist chunks., Adapts qdrant_store's free functions to the pipeline's QdrantSink protocol. (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.22
Nodes (16): CvProfile, _fold(), MatchResult, hr.match_role: score a CvProfile against job-relevant criteria (task 8.5, dept s, `criteria` is the role's required skills/qualifications (dept scenario     05's, score_role_match(), _profile(), agents.hr_agent.match: hr.match_role scoring (task 8.5, dept scenario 05 "match (+8 more)

### Community 73 - "Community 73"
Cohesion: 0.24
Nodes (15): InvoiceFields, Protocol, ReasoningClient, build_invoice_agent_graph(), ErpLike, InvoiceAgentState, OcrLike, Any (+7 more)

### Community 74 - "Community 74"
Cohesion: 0.12
Nodes (14): apps/runtime/core/llm (gateway client), Any, async_sessionmaker, Spend-ledger sink (task 2.3, TRD §5).  Appends one row per LLM call to ``spend, Async writer for spend_ledger rows over a SQLAlchemy session factory., SpendLedger, Cross-cutting rules honored, Deviations / deferrals (+6 more)

### Community 75 - "Community 75"
Cohesion: 0.18
Nodes (13): build_context(), Context, Any, Protocol, Conversation context budgeting: rolling window + summarized eviction (TRD §5)., The context to feed a call: an optional rolling summary plus recent turns., Split history into (summary of evicted turns, recent verbatim turns)., SummaryClient (+5 more)

### Community 76 - "Community 76"
Cohesion: 0.12
Nodes (16): Commit & Branch Convention, 1. Enable branch protection on `main` (GitHub side of task 1.0) — REQUIRED, Enable Branch Protection on main (pre-prod item), Must do before production, Production / Release Checklist, Deviations / deferrals, Notable issues resolved (symptom → root cause → fix), Sprint 1 Report — Repo, Stack, CI, Gateway (+8 more)

### Community 77 - "Community 77"
Cohesion: 0.31
Nodes (17): AnalyticsAnswer, AnalyticsCase, evaluate_analytics_case(), Run one case through the real Analytics agent pipeline (5.2)., _run_analytics_case(), evals.runner: Analytics eval assertion checking (task 5.2, dept scenario 02)., test_expect_row_count_fails_on_mismatch(), test_expect_row_count_passes_on_exact_match() (+9 more)

### Community 78 - "Community 78"
Cohesion: 0.25
Nodes (10): DevRunDialog(), ExampleCard(), ExampleOut, exampleTitle(), HrRunDialog(), InvoiceRunDialog(), DialogContent(), DialogDescription() (+2 more)

### Community 79 - "Community 79"
Cohesion: 0.32
Nodes (16): EvalCase, evaluate_case(), RagAnswer, _answer(), evals.runner: pure per-case assertion checking (task 4.4, TRD §13.4).  Asserti, test_case_result_is_a_dataclass_with_id_and_reason(), test_evaluate_case_combines_multiple_assertions_all_must_pass(), test_load_dataset_parses_jsonl_into_cases() (+8 more)

### Community 80 - "Community 80"
Cohesion: 0.12
Nodes (16): openapi-fetch, openapi-typescript, dependencies, openapi-fetch, devDependencies, openapi-typescript, typescript, typescript (+8 more)

### Community 81 - "Community 81"
Cohesion: 0.17
Nodes (13): AppError, ForbiddenError, install_error_handlers(), Exception, FastAPI, Domain error model and FastAPI exception handlers., Base class for domain errors mapped to HTTP responses., Register a handler that renders AppError as a structured JSON body. (+5 more)

### Community 82 - "Community 82"
Cohesion: 0.28
Nodes (14): Model, Model registry (TRD §4.1). Mirrored into the LiteLLM config., add_model(), delete_model(), get_model(), list_models(), ModelIn, ModelOut (+6 more)

### Community 83 - "Community 83"
Cohesion: 0.16
Nodes (12): _clamp_limit(), Any, Protocol, QueryRunner, pg_ro MCP tool: governed read-only SQL (task 5.1, dept scenario 02).  Enforces, _referenced_tables(), GovernedToolRefusal, Exception (+4 more)

### Community 84 - "Community 84"
Cohesion: 0.21
Nodes (14): compute_cost(), parse_usage(), Any, Token-usage parsing and cost computation (TRD §5).  Pure helpers: read an Open, Token counts for one LLM call., Extract token counts from an OpenAI-style response body., Compute USD cost. Cached input tokens are billed at the cached price; the     r, Usage (+6 more)

### Community 85 - "Community 85"
Cohesion: 0.13
Nodes (16): dependencies, clsx, @fleet/shared, next-intl, @radix-ui/react-tabs, @radix-ui/react-toast, react, react-dom (+8 more)

### Community 86 - "Community 86"
Cohesion: 0.16
Nodes (16): Rule 2: Sensitivity routing enforced, Presidio TR Name False-Positives on Common Nouns, Regex-Only PII Scrubber (core/pii_scrub.py), Invoice & Reconciliation Agent (Finance), Talent & Onboarding Agent (HR), Vehicle Intake Agent (Trink sat!), Failure Behavior & Fallbacks (§4.4), Local-Model Lane (Ollama/vLLM, pii) (+8 more)

### Community 87 - "Community 87"
Cohesion: 0.13
Nodes (15): 10. Legal Document Review — Legal [Wave 2], 1. Support Copilot — Customer Service [Wave 0], 2. Self-Service Analytics — Data [Wave 0], 3. Dev Agent — IT / Engineering [Wave 0], 4. Invoice & Reconciliation — Finance [Wave 0], 5. HR Talent & Onboarding — HR [Wave 0 partial → 1], 6. Listing Quality — Listings Operations [Wave 1], 7. Vehicle Intake — Trink sat! [Wave 1] (+7 more)

### Community 88 - "Community 88"
Cohesion: 0.15
Nodes (16): Dealer Onboarding — Corporate Sales, HR Talent & Onboarding — HR, embeddings tier (openai/text-embedding-3-small), Per-Model Fallback Chains, Proxy-Level Langfuse Callbacks, local-embeddings (ollama/bge-m3), Local PII Lane (Ollama, host-native GPU), local-reasoning (ollama/qwen2.5:7b-instruct-q4_K_M) (+8 more)

### Community 89 - "Community 89"
Cohesion: 0.23
Nodes (15): _admin_token(), backing_stack(), _client(), keycloak(), _provision_realm(), MonkeyPatch, TestClient, Integration test: 401 without/with a bad token, 200 with a valid member token, (+7 more)

### Community 90 - "Community 90"
Cohesion: 0.24
Nodes (10): _FakeBackend, fleet_mcp.servers.github: read_repo/create_branch/open_pr (task 5.3, dept scena, test_commit_file_with_agent_prefix_succeeds(), test_commit_file_without_agent_prefix_is_rejected(), test_contracts_declare_correct_risk_classes(), test_create_branch_with_agent_prefix_succeeds(), test_create_branch_without_agent_prefix_is_rejected(), test_open_pr_always_dispatches_regardless_of_content() (+2 more)

### Community 91 - "Community 91"
Cohesion: 0.21
Nodes (10): Records fleet_http_requests_total / fleet_http_request_duration_seconds     (ta, RequestMetricsMiddleware, _build_app(), _FakeRedis, _FakeResult, _FakeSession, FastAPI, GET /metrics (task 7.4): unauthenticated Prometheus exposition endpoint. Proves (+2 more)

### Community 92 - "Community 92"
Cohesion: 0.25
Nodes (14): Document, Uploaded source document (TRD §11)., DocumentOut, get_document(), list_documents(), _minio_client(), _object_key(), AsyncSession (+6 more)

### Community 93 - "Community 93"
Cohesion: 0.33
Nodes (14): MCPValidationError, Exception, Raised when a call_tool payload fails the tool's input_schema., ToolContract, _echo(), _make_server(), fleet_mcp.base: MCP server base — tool registry, risk_class, schema validation,, test_call_tool_missing_required_field_raises_validation_error() (+6 more)

### Community 94 - "Community 94"
Cohesion: 0.19
Nodes (10): InternalMockTool, Any, Exception, internal-mock MCP tool: fixture-backed stand-in for an internal API (task 5.1)., No fixture record exists for the given id., RecordNotFoundError, fleet_mcp.servers.internal_mock: fixture-backed internal API mock (task 5.1)., test_contract_declares_read_risk_class() (+2 more)

### Community 95 - "Community 95"
Cohesion: 0.21
Nodes (10): AgentSpec, LangGraph base graph shared by every agent (task 4.1, killswitch 4.2).  Node o, _tool_by_name(), ToolSpec, Integration: the runtime base graph against a REAL Postgres checkpointer (task, Always proposes the same write:external tool call, regardless of tier., _Resp, _send_email() (+2 more)

### Community 96 - "Community 96"
Cohesion: 0.29
Nodes (10): LLMClient, Governed entry point for LLM calls. Construct once per process with the     mod, _checker(), FakeLedger, FakeTransport, Budget enforcement inside the gateway client (task 2.4).  The client runs a bu, test_hard_stop_blocks_call_and_bills_nothing(), test_no_checker_means_no_enforcement() (+2 more)

### Community 97 - "Community 97"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, eslint-config-next, @eslint/eslintrc, @types/node, @types/react, @types/react-dom, typescript (+7 more)

### Community 98 - "Community 98"
Cohesion: 0.20
Nodes (9): AuditMiddleware, Request, Response, RateLimitMiddleware, Assign a trace_id per request and echo it in the response header., Write an append-only audit row for each request, carrying the trace_id., Fixed-window per-client rate limiting backed by Redis., TraceIdMiddleware (+1 more)

### Community 99 - "Community 99"
Cohesion: 0.26
Nodes (12): Right-to-erasure subject hashing (task 8.3, TRD §8).  A pure, deterministic hash, subject_hash(), _delete_conversations(), _delete_documents(), erase_subject(), ErasureResult, _minio_client(), _pseudonymize_audit_rows() (+4 more)

### Community 100 - "Community 100"
Cohesion: 0.18
Nodes (10): AsyncpgRunner, build_default_runner(), Any, Real QueryRunner for pg_ro.PgReadOnlyTool, over the `fleet_readonly` role (task, Integration: pg_ro MCP tool against the real dev-stack Postgres (task 5.1 AC —, Defense-in-depth: connect exactly as the runner does and confirm the DB     ses, test_live_query_against_fixture_sales_returns_rows(), test_live_query_on_non_allowlisted_table_never_reaches_db() (+2 more)

### Community 101 - "Community 101"
Cohesion: 0.21
Nodes (9): _build_metadata(), ProxyTransport, Any, HTTP transport to the LiteLLM proxy (task 2.3).  The proxy exposes an OpenAI-c, trace_id/agent_id/user_id/dept_id passthrough (TRD §6 trace correlation)     pl, Async transport that POSTs chat completions to the LiteLLM proxy., Send a completion; raise for a non-2xx so the client maps it to GatewayError., Send an embeddings request; raise for non-2xx (mapped to GatewayError). (+1 more)

### Community 102 - "Community 102"
Cohesion: 0.19
Nodes (14): Analytics fixture warehouse views, Sprint 1 — Repo, Stack, CI, Gateway, Task 1.1 — Monorepo + dev stack, Task 1.2 — CI + migrations + seed, Task 1.3 — Gateway auth core, Task 1.4 — Gateway cross-cutting middleware, Task 1.5 — Helm umbrella chart skeleton + k3d bootstrap, Sprint 1 Stage A Implementation Plan (+6 more)

### Community 103 - "Community 103"
Cohesion: 0.15
Nodes (14): Deferrable Tasks List, 3.4 Web Shell + Knowledge UI, HITL Interrupt Node, Agent Kill Switches, Sprint 4 — Runtime, Chat, First Agent, 4.1 Runtime Core, 4.2 Agent Registry + Semantic Cache + Kill Switches, 4.3 Chat UI (+6 more)

### Community 104 - "Community 104"
Cohesion: 0.34
Nodes (13): DevAgentAnswer, DevAgentCase, evaluate_dev_agent_case(), Run one case through the real Dev Agent graph (5.5) — real gateway     client,, _run_dev_agent_case(), evals.runner: Dev Agent eval assertion checking (task 5.5, dept scenario 03)., test_branch_name_must_start_with_agent_prefix(), test_expect_blocked_fails_when_run_reached_pending_approval() (+5 more)

### Community 105 - "Community 105"
Cohesion: 0.37
Nodes (12): Budget, Spend budget for a scope (TRD §5 budget hierarchy, §11)., BudgetIn, BudgetOut, create_budget(), delete_budget(), list_budgets(), AsyncSession (+4 more)

### Community 106 - "Community 106"
Cohesion: 0.21
Nodes (10): ExtractionParseError, Exception, The model's CV-extraction response was malformed or missing a field., HrAgentState, OcrLike, Any, Protocol, HR Agent graph: CV image -> OCR -> structured profile -> role match -> shortlist (+2 more)

### Community 107 - "Community 107"
Cohesion: 0.49
Nodes (12): validate_invoice(), _FakePoLookup, _fields(), _po(), agents.invoice_agent.validator: extracted fields -> validation against purchase, test_amount_mismatch_is_flagged_never_silently_ok(), test_duplicate_po_number_is_flagged(), test_matching_invoice_validates_ok() (+4 more)

### Community 108 - "Community 108"
Cohesion: 0.23
Nodes (11): attach_citations(), Citation, Any, Generic citation carrier for the graph's citation-attach node (TRD §9, §11 messa, Return a copy of response with a serialized citations list attached., GraphState, TypedDict, core.citations: generic citation shape + attach helper (task 4.1).  Agent-spec (+3 more)

### Community 109 - "Community 109"
Cohesion: 0.21
Nodes (7): _default_now(), _is_flag_set(), datetime, Protocol, Kill switches: per-agent pause + global read-only mode (TRD §9).  Per-agent `s, Current state of the global flag (task 6.5.3 — the Admin UI's         kill-swit, RedisLike

### Community 110 - "Community 110"
Cohesion: 0.24
Nodes (8): BudgetOut, BudgetsAdmin(), PERIODS, SCOPE_TYPES, TicketOut, SelectContent(), SelectItem(), SelectTrigger()

### Community 111 - "Community 111"
Cohesion: 0.15
Nodes (13): [DEFERRABLE] Task Marker, Sprint 9 — Hardening, Live Verification Catches What Mocks Cannot, Grafana Dangling Datasource UID Bug, Test Infra Config Against Real Binaries, CPU-Only Local Inference Throughput Finding, Measure Layer By Layer, Don't Assume, Two-Layer Timeout Mismatch (litellm 300s vs client 60s) (+5 more)

### Community 112 - "Community 112"
Cohesion: 0.15
Nodes (11): 15-Minute Demo Script, Implementation Plan · Sprint 10 — Demo Assembly & Docs, Sprint 10 — Demo Assembly & Docs, 10.1 Fresh-Install Rehearsal, 10.2 Docs + Release, 4.4 Support Copilot (Agent #1), Implementation Plan · Sprint 9 — Hardening, Sprint 9 — Hardening (+3 more)

### Community 113 - "Community 113"
Cohesion: 0.19
Nodes (12): 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, Implementation Plan · Sprint 5 — MCP, Agents #2–3, Approvals, MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue, 5.5 Dev Agent (Agent #3) (+4 more)

### Community 114 - "Community 114"
Cohesion: 0.15
Nodes (12): 4.10 Legal & Compliance — Document Review Assistant, 4.1 Customer Service — Support Copilot, 4.2 Listings Operations — Listing Quality Agent, 4.3 Trink sat! — Vehicle Intake Agent, 4.4 Human Resources — Talent & Onboarding Agent, 4.5 Finance — Invoice & Reconciliation Agent, 4.6 Marketing & Content — Insights Publisher, 4.7 Corporate Sales — Dealer Onboarding Agent (+4 more)

### Community 115 - "Community 115"
Cohesion: 0.17
Nodes (13): Everything-is-an-API Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), n8n (queue mode), RAG Service, Redis, Redis 7 + arq Workers, FastAPI / Python 3.12 (+5 more)

### Community 116 - "Community 116"
Cohesion: 0.21
Nodes (10): _extract_roles(), _fetch_jwks(), OIDC token validation: fetch Keycloak JWKS and verify RS256 bearer tokens., Verify a raw bearer token string and return the current user, or raise 401., Best-effort verified `sub` extraction from a raw Authorization header value., try_current_user_sub(), verify_bearer_token(), admin_only() (+2 more)

### Community 117 - "Community 117"
Cohesion: 0.24
Nodes (6): GitHubLike, JiraLike, Any, Protocol, Dev Agent graph: ticket -> plan -> branch -> PR -> Slack, single HITL interrupt, SlackLike

### Community 118 - "Community 118"
Cohesion: 0.21
Nodes (5): Any, Protocol, QueryTool, PurchaseOrder, _FakePoLookup

### Community 119 - "Community 119"
Cohesion: 0.29
Nodes (8): Prometheus metrics shared across the runtime (task 7.4, TRD §6/§13.5).  Regist, _checker(), _counter_value(), FakeLedger, FakeTransport, Prometheus metrics emitted by the gateway client's budget check (task 7.4).  `, test_soft_limit_call_increments_the_counter(), test_under_budget_call_does_not_increment_the_counter()

### Community 120 - "Community 120"
Cohesion: 0.23
Nodes (12): Sprint 2 — LLM Gateway, Model Registry, Budgets, Self-Service Analytics Agent (Text-to-SQL), Design Principles (gateway-everything, K8s-from-day-one), LangGraph Agent Runtime (Postgres checkpointer), LLM Gateway (LiteLLM Proxy), Qdrant Vector DB, Technology Stack (Decided), Fleet Technical Requirements & System Design (+4 more)

### Community 121 - "Community 121"
Cohesion: 0.17
Nodes (12): Sprint 3 — RAG, users.email_hash Always Empty (unmet pseudonymisation), Subject Erasure Endpoint (DELETE /v1/subjects/{hash}), Microsoft Presidio + TR Recognizers, Loki Structured Logs, Data Classification (sensitivity levels), PII Pipeline (Presidio + TR recognizers), Redaction Downgrade Rule (+4 more)

### Community 122 - "Community 122"
Cohesion: 0.17
Nodes (11): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, 1. Vision, 2. Problem Statement, Fleet AI Operations Platform, Problem Statement, Project Overview · Vision & Problem Statement (+3 more)

### Community 123 - "Community 123"
Cohesion: 0.23
Nodes (12): 6.3 Automation #2 — Invoice Intake, Knowledge Base (RAG), Dealer Onboarding Agent (Corporate Sales), Department Use Cases, Document Review Assistant (Legal & Compliance), Invoice & Reconciliation Agent (Finance), Listing Quality Agent, Self-Service Analytics Agent (Data & Analytics) (+4 more)

### Community 124 - "Community 124"
Cohesion: 0.17
Nodes (11): Global Constraints, Self-Review, Sprint 1 · Stage A — Monorepo Skeleton + Dev Stack Implementation Plan, Task 1: Root workspace files (uv + pnpm + tooling config), Task 2: Directory skeleton for all app/packages/infra trees, Task 3: Next.js 15 web skeleton (pnpm), Task 4: Environment template + Keycloak realm, Task 5: Observability provisioning files (Prometheus, Grafana, Loki, Alertmanager) (+3 more)

### Community 125 - "Community 125"
Cohesion: 0.17
Nodes (11): compilerOptions, declaration, esModuleInterop, module, moduleResolution, noEmit, skipLibCheck, strict (+3 more)

### Community 126 - "Community 126"
Cohesion: 0.24
Nodes (10): client(), _insert_spend(), TestClient, Integration: /v1/admin/budgets (task 7.1b) against real Postgres — create, list, Task 7.4's "UI warning" half of the soft-limit AC: list_budgets     computes re, Plain sync insert (psycopg2, no asyncio) — see test_users_admin_router_live.py's, test_create_then_list_then_update_then_delete(), test_duplicate_scope_and_period_rejected() (+2 more)

### Community 127 - "Community 127"
Cohesion: 0.24
Nodes (8): AsyncClient, Integration: full HR Agent chain against the real dev stack (task 8.5, dept scen, _render_cv_image_base64(), _set_common_env(), _start_run(), test_cv_run_reaches_approval_queue_without_protected_attributes(), test_reject_path_closes_the_shortlist_draft(), _token()

### Community 128 - "Community 128"
Cohesion: 0.29
Nodes (11): client(), _insert_user(), migrated_pg(), TestClient, Integration: /v1/admin/users and /v1/admin/departments (task 7.1) against real, Plain sync insert (psycopg2, no asyncio) so this setup never shares an     even, test_add_role_then_list_reflects_it(), test_duplicate_role_assignment_rejected() (+3 more)

### Community 129 - "Community 129"
Cohesion: 0.24
Nodes (3): _FakeGitHubBackend, _FakeJiraBackend, Any

### Community 130 - "Community 130"
Cohesion: 0.24
Nodes (6): Analytics agent's semantic layer: view/column glossary the SQL generator ground, SemanticLayer, ViewSpec, agents.analytics.semantic_layer: view/column glossary the SQL generator grounds, test_allowlisted_tables_match_view_names(), test_describe_renders_view_and_column_glossary()

### Community 131 - "Community 131"
Cohesion: 0.29
Nodes (7): PgPoLookup, Real PO lookup over pg_ro (task 6.3, dept scenario 04 "pg_ro.query purchase-ord, _FakeQueryTool, agents.invoice_agent.po_lookup: PgPoLookup over a pg_ro-shaped QueryTool (task, test_lookup_finds_matching_po(), test_lookup_never_interpolates_the_untrusted_po_number_into_sql(), test_lookup_returns_none_for_unknown_po()

### Community 132 - "Community 132"
Cohesion: 0.27
Nodes (9): Tool risk_class -> approval-queue decision (TRD §9).  Pure decision logic, no, Return True if a tool call of this risk_class must go through HITL., requires_approval(), core.hitl: tool risk_class -> autonomous vs approval-queue decision (TRD §9)., test_read_tool_never_requires_approval(), test_write_external_always_requires_approval(), test_write_internal_autonomous_when_pass_rate_and_autonomy_both_clear(), test_write_internal_requires_approval_when_autonomy_disabled() (+1 more)

### Community 133 - "Community 133"
Cohesion: 0.25
Nodes (7): CreateExampleDialog(), AgentSummary, ExampleOut, ExamplesGallery(), TabsContent(), TabsList(), TabsTrigger()

### Community 134 - "Community 134"
Cohesion: 0.24
Nodes (10): Cross-cutting rules honored, Deviations / deferrals, Sprint 3 Task 3.1 Ingestion pipeline, Sprint 3 Task 3.2 Collections + retention, Sprint 3 Task 3.3 Query + citations, Sprint 3 Task 3.4 Web shell + Knowledge UI, Notable issues resolved (symptom → root cause → fix), Sprint 3 Report — RAG (Ingestion, Collections, Query, Web Shell) (+2 more)

### Community 135 - "Community 135"
Cohesion: 0.24
Nodes (11): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.2 Ollama Host-Native with GPU, 0.4 Container-to-Host Ollama Reachability, Sensitivity Routing Enforcement, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy (+3 more)

### Community 136 - "Community 136"
Cohesion: 0.22
Nodes (10): docker-compose.dev.yml Stack, Implementation Plan · Sprint 1 — Repo, Stack, CI, Gateway, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack, 1.2 CI + Migrations + Seed, 1.3 Gateway Auth Core, 1.4 Gateway Cross-Cutting Middleware (+2 more)

### Community 137 - "Community 137"
Cohesion: 0.18
Nodes (10): Global Constraints, Self-Review, Sprint 1 · Stage B — CI + Migrations + Seed Implementation Plan, Task 1: Python deps + async DB layer in apps/api, Task 2: Alembic setup + first migration, Task 3: Seed script (synthetic data + analytics fixture views), Task 4: Makefile targets (test/migrate/seed/scan) + integration marker, Task 5: Minimal apps/api Dockerfile (+2 more)

### Community 138 - "Community 138"
Cohesion: 0.18
Nodes (10): Decisions (locked with the user), Delivery Stages, Dev Stack — `docker-compose.dev.yml` (11 services), Goal, Makefile Targets, Non-Goals (YAGNI), Repository Layout, Sprint 1 Foundation Design Spec (+2 more)

### Community 139 - "Community 139"
Cohesion: 0.20
Nodes (11): analytics eval entry, dev_agent eval entry, Per-Agent Eval Thresholds, hr_agent eval entry (threshold 0.90), invoice_agent eval entry, support_copilot eval entry, Seniority-Tiered Annual Leave Entitlement, Leave and Benefits Policy (HR fixture) (+3 more)

### Community 140 - "Community 140"
Cohesion: 0.35
Nodes (10): CvFixture, CvRehearsalResult, _field_hit(), _fold_ascii(), main(), _ocr_word_accuracy(), Task 8.1: local-lane quality rehearsal.  Renders synthetic TR CV "scans" (never, Word-level accuracy: fraction of ground-truth words found (ASCII-folded,     tol (+2 more)

### Community 141 - "Community 141"
Cohesion: 0.29
Nodes (8): _build_app(), FastAPI, fleet_api.routers.users_admin: users/roles admin CRUD (task 7.1). Only the RBAC, Raises if the router ever tries to use it — proves a code path never     reache, test_dept_admin_cannot_list_users(), test_member_cannot_list_users(), test_unknown_role_name_rejected_before_touching_db(), _UntouchedSession

### Community 142 - "Community 142"
Cohesion: 0.20
Nodes (9): name, private, scripts, build, dev, lint, start, typecheck (+1 more)

### Community 143 - "Community 143"
Cohesion: 0.20
Nodes (9): Global Constraints, Self-Review, Sprint 1 · Stage C — Auth Core, Middleware, Helm/k3d Implementation Plan, Task 1: Config, error model, and FastAPI app factory with health/readiness (1.3 part A), Task 2: OIDC validation + RBAC permission service + 401/403 integration tests (1.3 part B), Task 3: Cross-cutting middleware — trace_id, append-only audit, Redis rate limiter (1.4 part A), Task 4: OpenAPI → generated TypeScript client in packages/shared (1.4 part B), Task 5: Helm umbrella chart + values-dev + k3d bootstrap (1.5) (+1 more)

### Community 144 - "Community 144"
Cohesion: 0.42
Nodes (8): MockTransport, _client_with_transport(), fleet_api.n8n_client: async client over n8n's REST API + webhooks (task 6.5.3)., test_401_surfaces_as_auth_error_not_unreachable(), test_connect_error_surfaces_as_unreachable_not_raised(), test_list_workflows_happy_path(), test_set_active_calls_correct_endpoint(), test_trigger_webhook_json_posts_body()

### Community 145 - "Community 145"
Cohesion: 0.33
Nodes (6): Integration: full Dev Agent chain against the real dev stack + sandbox GitHub r, _set_common_env(), test_approve_path_opens_real_pr_on_sandbox(), test_reject_path_never_opens_a_pr(), test_unlabeled_ticket_is_blocked_before_any_branch_creation(), _token()

### Community 146 - "Community 146"
Cohesion: 0.27
Nodes (7): _build_app(), FastAPI, fleet_api.routers.subjects: right-to-erasure endpoint (task 8.3, TRD §8). Only t, Erasure is a platform-tier action (same gate as users_admin/budgets_admin),, test_dept_admin_cannot_erase_a_subject(), test_member_cannot_erase_a_subject(), _UntouchedSession

### Community 147 - "Community 147"
Cohesion: 0.31
Nodes (9): _app_session_factory(), get_session(), async_sessionmaker, AsyncSession, Build an async session factory bound to the given engine., Process-wide session factory over a single engine (built lazily)., FastAPI dependency yielding a request-scoped async session., session_factory() (+1 more)

### Community 148 - "Community 148"
Cohesion: 0.28
Nodes (7): Drop the cached engine/session factory so the next `get_session()`     call bui, reset_engine_cache(), client(), TestClient, Integration: GET /metrics (task 7.4) against real Postgres + Redis — the dept d, test_metrics_includes_dept_daily_spend_from_seeded_traffic(), test_metrics_includes_real_queue_depth()

### Community 149 - "Community 149"
Cohesion: 0.28
Nodes (6): ErpTool, Any, fleet_mcp.servers.erp: mock ERP create_draft_entry (task 6.3, dept scenario 04)., test_contract_declares_write_external(), test_create_draft_entry_records_and_returns_a_draft(), test_each_draft_entry_gets_a_unique_id()

### Community 150 - "Community 150"
Cohesion: 0.25
Nodes (6): build_default_sender(), Protocol, slack MCP tool: slack.post via incoming webhook (task 5.3, dept scenario 03)., Real transport: one incoming-webhook URL per Fleet deployment. Slack     incomi, SlackWebhookSender, WebhookSender

### Community 151 - "Community 151"
Cohesion: 0.25
Nodes (5): build_default_sender(), Real SMTP transport for email.EmailSendTool (task 5.1).  Talks to the sandbox, SmtpSender, Integration: email MCP tool against the real mailpit SMTP sandbox (task 5.1 AC, test_live_send_lands_in_mailpit()

### Community 152 - "Community 152"
Cohesion: 0.25
Nodes (6): metadata, ToastContext, ToastMessage, ToastProvider(), ToastVariant, variantClass

### Community 153 - "Community 153"
Cohesion: 0.22
Nodes (9): Rule 3: External side effects via MCP with risk_class, Agent Hub, Control Plane (guardrails, HITL, eval, audit), Dev Agent (IT / Engineering), Fleet — AI Operations Platform (Overview), Integration Layer (MCP), Knowledge Base (RAG), Support Copilot (Customer Service agent) (+1 more)

### Community 154 - "Community 154"
Cohesion: 0.25
Nodes (9): Turkish Text Folding & Fuzzy Vendor Matching, Untyped JSON eval_cases Payload Storage, HR Eval 47% → 100% Root-Cause Analysis, Fix the Product, Not the Eval Assertion, Fixture Renderer Canvas-Height Clipping Bug, Synthetic Document Image Renderer (real TTF), Tesseract tur+eng Local OCR Path, Examples Backend (eval_cases + /v1/examples) (+1 more)

### Community 155 - "Community 155"
Cohesion: 0.22
Nodes (9): Keycloak fleet realm with five test users, Alembic first migration (0001_initial), fleet_readonly read-only DB role, GitHub Actions CI pipeline (lint/unit/integration/security/build), FastAPI app factory (create_app), Keycloak aud claim mismatch risk, Cross-cutting middleware (trace_id, audit, rate-limit), OIDC token validation (Keycloak JWKS RS256) (+1 more)

### Community 156 - "Community 156"
Cohesion: 0.22
Nodes (7): @playwright/test, devDependencies, @playwright/test, name, private, scripts, test

### Community 157 - "Community 157"
Cohesion: 0.39
Nodes (6): Integration: full Invoice Agent chain against the real dev stack (task 6.3 AC:, _render_invoice_image_base64(), _set_common_env(), test_matching_invoice_reaches_approval_queue_with_extracted_fields(), test_reject_path_never_creates_a_draft_entry(), _token()

### Community 158 - "Community 158"
Cohesion: 0.25
Nodes (4): async_sessionmaker, Integration: spend_ledger writes + budget pre-check aggregate against a real Po, _seed_spend(), _sf()

### Community 160 - "Community 160"
Cohesion: 0.25
Nodes (3): _names(), Static validation of the pinned LiteLLM config (task 2.1).  Guards the shape L, test_all_fallback_targets_are_defined_models()

### Community 161 - "Community 161"
Cohesion: 0.43
Nodes (7): _collection_id(), main(), Any, async_sessionmaker, Seed demo KBs (task 4.4 Support Copilot + task 8.5 HR Onboarding): upload evals, seed_docs(), _upsert_document()

### Community 162 - "Community 162"
Cohesion: 0.25
Nodes (7): _amount_mismatches(), check_duplicate(), PoNotFoundError, Exception, Extracted fields -> validation against purchase records (task 6.3, dept scenari, No purchase order exists for the extracted po_number., True if this PO number has already been processed this run/session —     the de

### Community 163 - "Community 163"
Cohesion: 0.29
Nodes (3): CostDashboard(), CostSummaryOut, SpendByKey

### Community 164 - "Community 164"
Cohesion: 0.36
Nodes (5): badgeVariant(), clearanceLabelKey, clearanceVariant(), ModelOut, ModelsAdmin()

### Community 165 - "Community 165"
Cohesion: 0.39
Nodes (4): ScenarioCard(), Scenario, SCENARIOS, ScenarioStatus

### Community 166 - "Community 166"
Cohesion: 0.25
Nodes (7): Dev setup bootstrap (task 10.1), Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four environments (local/test/demo-staging/prod), Shared Helm chart (per-env values), Dev setup (bootstrap — finalized in task 10.1), fleet-workflow

### Community 167 - "Community 167"
Cohesion: 0.25
Nodes (7): 3.1 Agent Hub, 3.2 Workflow Studio (n8n), 3.3 Knowledge Base (RAG), 3.4 Integration Layer (MCP), 3.5 Control Plane, 3. Solution: The Fleet Platform, Project Overview · Solution: The Five Core Modules

### Community 168 - "Community 168"
Cohesion: 0.25
Nodes (8): Secure and Observable by Default, Langfuse (self-hosted), Prompt Caching, Semantic Cache, Trace ID Correlation, Langfuse LLM Layer (traces/generations), Output Guards (RAG grounding check), Evaluation (golden sets)

### Community 169 - "Community 169"
Cohesion: 0.25
Nodes (7): 6.1 Correlation [CORE], 6.2 LLM layer — Langfuse [CORE], 6.3 Metrics — Prometheus/Grafana [CORE], 6.4 Logs — Loki [CORE], 6.5 Alerting [CORE], 6. Observability: Logs, Traces, Agent & Model Performance, TRD · Observability (§6)

### Community 170 - "Community 170"
Cohesion: 0.29
Nodes (7): _render_invoice_image_base64(), _load_readable_font(), Shared synthetic document image rendering for evals/rehearsals that need a reali, Render `lines` as a simple white-background "document scan" PNG, base64-encoded., render_document_image_base64(), FreeTypeFont, ImageFont

### Community 171 - "Community 171"
Cohesion: 0.39
Nodes (8): CI job: build-image (docker build + trivy scan), CI job: integration (pytest tests/integration, testcontainers), CI job: lint (ruff + mypy), CI job: security (bandit + gitleaks), CI job: unit (pytest tests/unit), CI GitHub Actions workflow, gitleaks/gitleaks-action@v2, Trivy scan via aquasec/trivy docker image (not trivy-action)

### Community 172 - "Community 172"
Cohesion: 0.25
Nodes (5): MonkeyPatch, Path, Integration: eval_cases seeding (task 6.5.2) is idempotent and matches evals/da, test_promote_round_trips_a_user_case_into_jsonl_and_load_dataset(), test_seed_eval_cases_is_idempotent_and_matches_jsonl_counts()

### Community 173 - "Community 173"
Cohesion: 0.36
Nodes (7): client(), TestClient, Integration: /v1/admin/cost/summary and /v1/admin/audit (task 7.2) against real, test_audit_filter_by_actor(), test_audit_list_includes_langfuse_deep_link(), test_cost_summary_renders_seeded_traffic(), test_seed_observability_demo_is_idempotent()

### Community 174 - "Community 174"
Cohesion: 0.29
Nodes (6): Cross-cutting rules honored, Deviations / deferrals, Notable issues resolved (symptom → root cause → fix), Sprint 4 Report — Agent Runtime, Chat, First Agent, Tasks & Acceptance Criteria, What was tested and how

### Community 175 - "Community 175"
Cohesion: 0.38
Nodes (7): LiteLLM Proxy, Ollama (dev local models), vLLM (prod GPU), Fallback Chains & Circuit Breaking, Budget Hierarchy, Local-Model Lane (pii/confidential), Reference Sizing

### Community 176 - "Community 176"
Cohesion: 0.29
Nodes (6): 4.1 Model Registry [CORE], 4.2 Default Model Matrix [CORE], 4.3 Routing & Tiering [CORE], 4.4 Failure behavior [CORE], 4. Model Management & LLM Gateway, TRD · Model Management & LLM Gateway (§4)

### Community 177 - "Community 177"
Cohesion: 0.29
Nodes (7): Routing & Tiering (utility/reasoning), Model Tiering (utility vs reasoning), Spend Ledger, Retention & Right to Erasure, agents Table, audit_log Table (append-only), PostgreSQL Core Tables

### Community 178 - "Community 178"
Cohesion: 0.33
Nodes (7): Sensitivity Clearance Ordering, Sensitivity Routing (KVKK), OWASP LLM Top 10 Mapping, Approval Queue (HITL), Tool Risk Class, Integration Tests (testcontainers), CI/CD Pipeline (GitHub Actions)

### Community 179 - "Community 179"
Cohesion: 0.29
Nodes (6): name, packageManager, private, scripts, build, lint

### Community 180 - "Community 180"
Cohesion: 0.29
Nodes (3): Integration: JIT user provisioning + DB-backed role bootstrap (task 7.1).  Pro, The literal 7.1 AC: an admin edit to the roles table changes what     permissio, test_admin_role_edit_is_visible_on_next_load()

### Community 181 - "Community 181"
Cohesion: 0.33
Nodes (5): configure_tracing(), new_trace_id(), OpenTelemetry setup (dev: logging exporter) and trace-id helpers., Install a console span exporter once (dev default per plan/TRD §14)., Generate a request trace id.

### Community 182 - "Community 182"
Cohesion: 0.33
Nodes (5): healthz(), Liveness and readiness endpoints., Liveness: the process is up., Readiness: the database is reachable., readyz()

### Community 184 - "Community 184"
Cohesion: 0.33
Nodes (6): Dev Agent — IT / Engineering, Self-Service Analytics — Data, Sprint 5 — MCP, Agents #2-3, Approvals, Task 5.1 — MCP base + first servers, Task 5.2 — Analytics agent (agent #2), Task 5.5 — Dev Agent (agent #3)

### Community 185 - "Community 185"
Cohesion: 0.40
Nodes (5): Implementation Plan · Sprint 3 — RAG, Sprint 3 — RAG, 3.1 Ingestion Pipeline, 3.2 Collections + Retention, 3.3 Query + Citations

### Community 186 - "Community 186"
Cohesion: 0.40
Nodes (5): Implementation Plan · Sprint 6 — n8n Automations, Sprint 6 — n8n Automations, 6.1 n8n Queue Mode + API Keys, 6.2 Automation #1 — Weekly Summary, Insights Publisher (Marketing)

### Community 187 - "Community 187"
Cohesion: 0.33
Nodes (5): 5. Technology Coverage Map, 6. Rollout Strategy, 7. Success Metrics (Platform-Level), 8. Why This Approach Wins, Project Overview · Tech Coverage, Rollout, Metrics

### Community 188 - "Community 188"
Cohesion: 0.40
Nodes (6): Gateway-Everything Principle, LLM Gateway (LiteLLM Proxy), MCP Servers, Observability Stack (Langfuse/Prometheus/Grafana/Loki), Default Model Matrix, Model Registry

### Community 189 - "Community 189"
Cohesion: 0.33
Nodes (6): Keycloak (OIDC), Web UI (Next.js/TS), Next.js 15 Frontend, AuthN/AuthZ (Keycloak OIDC + RBAC), RBAC Role Matrix, E2E Tests (Playwright)

### Community 190 - "Community 190"
Cohesion: 0.33
Nodes (5): 7.1 AuthN/AuthZ [CORE], 7.2 Application & platform security [CORE], 7.3 LLM-specific security (OWASP LLM Top 10 mapping) [CORE], 7. Security, TRD · Security (§7)

### Community 191 - "Community 191"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 192 - "Community 192"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat endpoint's Analytics reply path against the real dev stack (t, test_analytics_reply_shows_sql_for_a_business_question()

### Community 193 - "Community 193"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: chat SSE + feedback against the real dev stack (task 4.3 AC: "stre, test_chat_stream_renders_answer_and_feedback_lands_in_langfuse()

### Community 194 - "Community 194"
Cohesion: 0.33
Nodes (3): Integration: infra/compose/prometheus/alerts.yml's rules actually fire (or don', Real amtool routing resolution against the same config template +     substitut, test_budget_soft_limit_alert_routes_to_slack_receiver()

### Community 195 - "Community 195"
Cohesion: 0.40
Nodes (3): _builder_token(), Integration: `/v1/rag/query` end to end against the real dev-stack (task 3.3 AC, test_rag_query_returns_grounded_answer_with_citations()

### Community 196 - "Community 196"
Cohesion: 0.50
Nodes (3): Any, Protocol, ReasoningUtilityClient

### Community 197 - "Community 197"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 198 - "Community 198"
Cohesion: 0.40
Nodes (4): JWT, next-auth, next-auth/jwt, Session

### Community 199 - "Community 199"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 200 - "Community 200"
Cohesion: 0.40
Nodes (5): Security Testing (trivy/bandit/semgrep/ZAP/garak), Prometheus/Grafana Metrics, Prompt Injection Defense (quarantine blocks), Security Tests (garak/injection corpus), Risks & Mitigations

### Community 201 - "Community 201"
Cohesion: 0.40
Nodes (5): 4. Planlanan Sprintler (7–10), Sprint 10 — Demo Kurgusu & Dokümantasyon, Sprint 7 — Yönetim Paneli & Gözlemlenebilirlik, Sprint 8 — KVKK Şeridi, Sprint 9 — Sertleştirme (Hardening)

### Community 202 - "Community 202"
Cohesion: 0.60
Nodes (4): Alembic environment. Uses a sync psycopg2 URL derived from FLEET_DATABASE_URL., run_migrations_offline(), run_migrations_online(), _sync_url()

### Community 203 - "Community 203"
Cohesion: 0.50
Nodes (3): _builder_token(), Integration: `/v1/admin/agents` CRUD + pause/resume against the real dev stack, test_agent_crud_and_pause_blocks_a_real_graph_run()

### Community 206 - "Community 206"
Cohesion: 0.50
Nodes (3): _builder_token(), Integration: PII masking in logs/traces against the real dev-stack (task 8.4 AC:, test_pii_conversation_masked_in_loki_and_langfuse()

### Community 208 - "Community 208"
Cohesion: 0.67
Nodes (3): main(), Create LangGraph's Postgres checkpointer tables (`checkpoints`, `checkpoint_blob, _setup()

### Community 209 - "Community 209"
Cohesion: 0.50
Nodes (4): Invoice & Reconciliation — Finance, Vehicle Intake — Trink sat!, Sprint 6 — n8n Automations, Task 6.3 — Automation #2 invoice intake

### Community 210 - "Community 210"
Cohesion: 0.50
Nodes (3): Department Scenarios · Wave Plan Overview & Spec Template, Fleet — Department Scenario Playbooks, Wave Plan Overview

### Community 211 - "Community 211"
Cohesion: 0.50
Nodes (3): Deferrable Tasks, Demo Script (15 min), Implementation Plan · Demo Script & Deferrable Tasks

### Community 212 - "Community 212"
Cohesion: 0.50
Nodes (3): 1. Goals, Non-Goals, Design Principles, Fleet — Technical Requirements & System Design Document, TRD · Goals, Non-Goals, Design Principles (§1)

### Community 213 - "Community 213"
Cohesion: 0.50
Nodes (3): 15. Phase Map (what ships when), 16. Risks, TRD · Phase Map & Risks (§15–16)

### Community 214 - "Community 214"
Cohesion: 0.67
Nodes (3): main(), promote(), Promote UI-created examples (eval_cases.source='user') into the versioned jsonl

### Community 215 - "Community 215"
Cohesion: 0.67
Nodes (3): openapi.json (dumped API schema), @fleet/shared, src/schema.d.ts (generated, do not hand-edit)

### Community 232 - "Community 232"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 238 - "Community 238"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

### Community 247 - "Community 247"
Cohesion: 0.67
Nodes (3): Nightly GitHub Actions Workflow, Nightly e2e Job, Nightly eval Job

## Ambiguous Edges - Review These
- `Self-Service Analytics Agent (Text-to-SQL)` → `Qdrant Vector DB`  [AMBIGUOUS]
  docs/source/PROJECT_OVERVIEW.md · relation: conceptually_related_to

## Knowledge Gaps
- **528 isolated node(s):** `metadata`, `ApprovalOut`, `AgentSummary`, `ChatMessage`, `FeedbackState` (+523 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **91 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Self-Service Analytics Agent (Text-to-SQL)` and `Qdrant Vector DB`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `build_client()` connect `Approval Resume Adapters` to `Community 96`, `Community 161`, `Community 101`, `Model Registry & Probes`, `Community 71`, `Community 40`, `Chat Data Model`, `Community 70`, `Community 104`, `Community 140`, `Community 77`, `Community 46`, `RBAC & Collections`, `Eval Runner`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `query()` connect `RBAC & Collections` to `Citations & Grounding`, `Approval Resume Adapters`, `Object & Vector Stores`, `Community 70`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `LLMClient` connect `Community 96` to `Erasure & PII Lane Tests`, `Community 71`, `LLM Gateway Client`, `Chat Data Model`, `Community 119`, `Gateway Client Tests`, `Approval Resume Adapters`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `CurrentUser` (e.g. with `Settings` and `Permission`) actually correct?**
  _`CurrentUser` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `KillSwitch` (e.g. with `AgentIn` and `AgentOut`) actually correct?**
  _`KillSwitch` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `Settings` (e.g. with `CurrentUser` and `AgentIn`) actually correct?**
  _`Settings` has 28 INFERRED edges - model-reasoned connections that need verification._
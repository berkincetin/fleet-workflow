# Graph Report - .  (2026-07-14)

## Corpus Check
- 50 files · ~35,179 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 274 nodes · 363 edges · 19 communities (13 shown, 6 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 81 edges (avg confidence: 0.81)
- Token cost: 357,384 input · 20,000 output

## Community Hubs (Navigation)
- CLAUDE.md Workflow & Protocol
- Gateway, Models & Security Stack
- MCP, Approvals & Automations (Sprints 5-6)
- Platform Architecture & Modules
- Cost, Budgets & Model Governance
- Agent Runtime & Kill Switches (Sprint 4)
- Repo, CI & Demo Assembly (Sprints 1,10)
- Prerequisites & LLM Gateway (Sprints 0,2)
- Department Agents (10 scenarios)
- Load, Alerting & SLOs
- AI-First Method & AC
- Kubernetes & Environments
- Data Stores & Backup/DR
- Testing Philosophy
- Data Plane
- OCR Pipeline
- Context Budgeting
- Platform Security
- Kill Switches

## God Nodes (most connected - your core abstractions)
1. `Fleet Technical Requirements & System Design (TRD)` - 16 edges
2. `Fleet Implementation Plan (Sprint Backlog)` - 15 edges
3. `Wave Plan (department onboarding waves 0-2)` - 12 edges
4. `Department Scenarios Wave Plan & Spec Template` - 12 edges
5. `Department Use Cases` - 10 edges
6. `Fleet AI Operations Platform` - 9 edges
7. `Fleet Platform CLAUDE.md Guidance` - 7 edges
8. `Privacy & KVKK` - 7 edges
9. `Five Core Modules` - 7 edges
10. `Local-Model Lane (Ollama/vLLM)` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Non-Negotiable Rules` --conceptually_related_to--> `Prompt Injection Defense (Quarantine)`  [INFERRED]
  CLAUDE.md → docs/TECHNICAL_REQUIREMENTS.md
- `Non-Negotiable Rules` --conceptually_related_to--> `LLM Gateway (LiteLLM Proxy)`  [INFERRED]
  CLAUDE.md → docs/TECHNICAL_REQUIREMENTS.md
- `Non-Negotiable Rules` --conceptually_related_to--> `Sensitivity Routing (KVKK)`  [INFERRED]
  CLAUDE.md → docs/TECHNICAL_REQUIREMENTS.md
- `Fleet Platform CLAUDE.md Guidance` --references--> `Fleet Technical Requirements & System Design (TRD)`  [EXTRACTED]
  CLAUDE.md → docs/TECHNICAL_REQUIREMENTS.md
- `Non-Negotiable Rules` --conceptually_related_to--> `Tool risk_class Classification`  [INFERRED]
  CLAUDE.md → docs/TECHNICAL_REQUIREMENTS.md

## Hyperedges (group relationships)
- **KVKK Sensitivity Routing Flow** — docs_technical_requirements_pii_pipeline, docs_technical_requirements_redaction_downgrade, docs_technical_requirements_sensitivity_routing, docs_technical_requirements_local_model_lane, docs_technical_requirements_clearance_rules [INFERRED 0.85]
- **Write-External Guardrail & HITL Flow** — docs_technical_requirements_risk_class, docs_technical_requirements_approval_queue, docs_project_overview_control_plane, docs_split_department_scenarios_03_dev_agent_dev_agent [INFERRED 0.75]
- **Fleet Five Core Modules** — docs_project_overview_agent_hub, docs_project_overview_workflow_studio, docs_project_overview_knowledge_base_rag, docs_project_overview_integration_layer_mcp, docs_project_overview_control_plane [EXTRACTED 1.00]
- **HITL Approval Flow (interrupt to queue to resume)** — docs_split_implementation_plan_sprint_4_runtime_chat_first_agent_hitl_interrupt_node, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_task_5_4_approval_queue, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_write_external, docs_split_project_overview_02_platform_modules_control_plane [EXTRACTED 0.90]
- **KVKK Local Model Lane (no cloud egress for pii)** — docs_split_implementation_plan_sprint_8_kvkk_lane_no_cloud_egress_guarantee, docs_split_implementation_plan_sprint_2_llm_gateway_budgets_sensitivity_routing_enforcement, docs_split_implementation_plan_sprint_0_prerequisites_task_0_2_ollama_gpu, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.85]
- **Demo Script Agent Showcase** — docs_split_implementation_plan_sprint_4_runtime_chat_first_agent_task_4_4_support_copilot, docs_split_implementation_plan_sprint_5_mcp_agents_approvals_task_5_5_dev_agent, docs_split_implementation_plan_sprint_6_n8n_automations_task_6_3_invoice_intake, docs_split_implementation_plan_sprint_8_kvkk_lane_task_8_2_hr_cv_mini_flow [EXTRACTED 0.90]
- **KVKK Sensitivity Routing Flow** — docs_split_technical_requirements_08_privacy_kvkk_data_classification, docs_split_technical_requirements_08_privacy_kvkk_pii_pipeline, docs_split_technical_requirements_08_privacy_kvkk_redaction_downgrade, docs_split_technical_requirements_04_model_management_gateway_sensitivity_routing, docs_split_technical_requirements_08_privacy_kvkk_local_model_lane [EXTRACTED 0.90]
- **Cost Governance Stack** — docs_split_technical_requirements_05_cost_token_optimization_budget_hierarchy, docs_split_technical_requirements_05_cost_token_optimization_spend_ledger, docs_split_technical_requirements_05_cost_token_optimization_cost_anomaly_alerts, docs_split_technical_requirements_03_tech_stack_litellm [EXTRACTED 0.85]
- **Guardrails & HITL Approval Flow** — docs_split_technical_requirements_09_guardrails_hitl_tool_risk_class, docs_split_technical_requirements_09_guardrails_hitl_approval_queue, docs_split_technical_requirements_03_tech_stack_langgraph, docs_split_technical_requirements_11_data_model_core_tables [EXTRACTED 0.85]
- **Agents whose write:external actions are always approval-gated** — agent_dev_agent, agent_invoice_agent, agent_insights_publisher, agent_dealer_onboarding, concept_hitl_approval_queue, concept_risk_class [EXTRACTED 1.00]

## Communities (19 total, 6 thin omitted)

### Community 0 - "CLAUDE.md Workflow & Protocol"
Cohesion: 0.06
Nodes (51): Commit & Branch Convention, Docs Split Token-Discipline Workflow, Fleet Platform CLAUDE.md Guidance, Mandatory Skills (superpowers + graphify), Non-Negotiable Rules, docs/PROGRESS.md Durable Memory, Task Execution Protocol, 15-Minute Demo Script (+43 more)

### Community 1 - "Gateway, Models & Security Stack"
Cohesion: 0.06
Nodes (40): Secure and Observable by Default, Langfuse (self-hosted), LiteLLM Proxy, Ollama (dev local models), Microsoft Presidio + TR Recognizers, Security Testing (trivy/bandit/semgrep/ZAP/garak), vLLM (prod GPU), Fallback Chains & Circuit Breaking (+32 more)

### Community 2 - "MCP, Approvals & Automations (Sprints 5-6)"
Cohesion: 0.10
Nodes (30): 0.3 Sandbox GitHub Repo + PAT + Slack Webhook, MCP Tool risk_class, Sprint 5 — MCP, Agents #2-3, Approvals, 5.1 MCP Base + First Servers, 5.2 Analytics Agent (Agent #2), 5.3 Jira/GitHub/Slack MCP, 5.4 Approval Queue, 5.5 Dev Agent (Agent #3) (+22 more)

### Community 3 - "Platform Architecture & Modules"
Cohesion: 0.08
Nodes (29): Everything-is-an-API Principle, Gateway-Everything Principle, Agent Runtime (LangGraph), API Gateway (FastAPI), Keycloak (OIDC), LLM Gateway (LiteLLM Proxy), MCP Servers, n8n (queue mode) (+21 more)

### Community 4 - "Cost, Budgets & Model Governance"
Cohesion: 0.09
Nodes (27): Sprint 2 — LLM Gateway, Model Registry, Budgets, Rollout Modes (assist/supervised/autonomous), Generic Department Onboarding Checklist, Budget Hierarchy, Sensitivity Clearance Rules, Cost & Token Optimization, PostgreSQL Data Model, Default Model Matrix (+19 more)

### Community 5 - "Agent Runtime & Kill Switches (Sprint 4)"
Cohesion: 0.09
Nodes (25): Deferrable Task Marker, Implementation Plan Goal, Ordered Sprint Task Model, Deferrable Tasks List, 2.2 Model Registry, HITL Interrupt Node, Agent Kill Switches, Sprint 4 — Runtime, Chat, First Agent (+17 more)

### Community 6 - "Repo, CI & Demo Assembly (Sprints 1,10)"
Cohesion: 0.12
Nodes (20): 15-Minute Demo Script, Sprint 10 — Demo Assembly & Docs, 10.1 Fresh-Install Rehearsal, 10.2 Docs + Release, docker-compose.dev.yml Stack, Sprint 1 — Repo, Stack, CI, Gateway, 1.0 Git & GitHub Bootstrap, 1.1 Monorepo + Dev Stack (+12 more)

### Community 7 - "Prerequisites & LLM Gateway (Sprints 0,2)"
Cohesion: 0.14
Nodes (18): Sprint 0 — Prerequisites, 0.1 API Keys in .env, 0.2 Ollama Host-Native with GPU, 0.4 Container-to-Host Ollama Reachability, Sensitivity Routing Enforcement, spend_ledger, Sprint 2 — LLM Gateway, Registry, Budgets, 2.1 LiteLLM Proxy (+10 more)

### Community 8 - "Department Agents (10 scenarios)"
Cohesion: 0.19
Nodes (12): Self-Service Analytics Agent (Data), Dealer Onboarding Agent (Corporate Sales), Dev Agent (IT/Engineering), HR Talent & Onboarding Agent(s) (HR), Insights Publisher Agent (Marketing), Invoice & Reconciliation Agent (Finance), Legal Document Review Agent (Legal), Listing Quality Agent (Listings Ops) (+4 more)

### Community 9 - "Load, Alerting & SLOs"
Cohesion: 0.40
Nodes (5): k6 Load Testing, Cost Anomaly Alerts, Alertmanager → Slack Alerting, SLO Targets, Load Tests (k6 scripts)

### Community 10 - "AI-First Method & AC"
Cohesion: 0.67
Nodes (3): Acceptance Criteria (AC), AI-First Development Method, Task Execution Protocol

### Community 11 - "Kubernetes & Environments"
Cohesion: 0.67
Nodes (3): Kubernetes from Day One, Helm Umbrella Chart + k3d + GitHub Actions, Four Environments (local/test/staging/prod)

### Community 12 - "Data Stores & Backup/DR"
Cohesion: 0.67
Nodes (3): MinIO (S3 Object Storage), Qdrant Vector DB, Backup / DR (PITR, snapshots)

## Knowledge Gaps
- **74 isolated node(s):** `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)`, `Listing Quality Agent (Listings Ops)`, `Insights Publisher Agent (Marketing)`, `docs/PROGRESS.md Durable Memory` (+69 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Fleet Technical Requirements & System Design (TRD)` connect `Cost, Budgets & Model Governance` to `CLAUDE.md Workflow & Protocol`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `15-Minute Demo Script` connect `Repo, CI & Demo Assembly (Sprints 1,10)` to `MCP, Approvals & Automations (Sprints 5-6)`, `Prerequisites & LLM Gateway (Sprints 0,2)`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `4.4 Support Copilot (Agent #1)` connect `Repo, CI & Demo Assembly (Sprints 1,10)` to `MCP, Approvals & Automations (Sprints 5-6)`, `Agent Runtime & Kill Switches (Sprint 4)`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `Generic Onboarding Checklist (new department)`, `Self-Service Analytics Agent (Data)`, `Dev Agent (IT/Engineering)` to the rest of the system?**
  _83 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CLAUDE.md Workflow & Protocol` be split into smaller, more focused modules?**
  _Cohesion score 0.06431372549019608 - nodes in this community are weakly interconnected._
- **Should `Gateway, Models & Security Stack` be split into smaller, more focused modules?**
  _Cohesion score 0.057692307692307696 - nodes in this community are weakly interconnected._
- **Should `MCP, Approvals & Automations (Sprints 5-6)` be split into smaller, more focused modules?**
  _Cohesion score 0.09885057471264368 - nodes in this community are weakly interconnected._
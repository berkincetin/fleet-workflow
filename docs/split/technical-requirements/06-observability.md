# TRD · Observability (§6)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 6. Observability: Logs, Traces, Agent & Model Performance

### 6.1 Correlation [CORE]
Every request gets `trace_id` at the API gateway, propagated via OpenTelemetry through agent nodes → MCP tool calls → LLM calls. One click from an audit row or a Grafana panel to the full Langfuse trace.

### 6.2 LLM layer — Langfuse [CORE]
- **Traces/generations:** every agent run with per-step spans: model, prompt version, input/output (PII-scrubbed), tokens, cost, latency, tool calls with arguments/results (redacted by policy).
- **Prompt registry link:** prompt versions registered in Langfuse; each generation records which version served it → regression diagnosis after prompt changes.
- **User feedback:** 👍/👎 + reason from chat UI → Langfuse scores API.
- **Eval integration:** golden datasets stored as Langfuse datasets; eval runs (see §13.4) write scores back; dashboards show per-agent quality trend per release.

### 6.3 Metrics — Prometheus/Grafana [CORE]
Key series: `http_request_duration_seconds{route}`, `agent_runs_total{agent,status}`, `agent_run_duration_seconds{agent}`, `llm_tokens_total{model,type=input|output|cached}`, `llm_cost_usd_total{model,dept}`, `tool_calls_total{tool,status}`, `guardrail_blocks_total{type}`, `approvals_pending`, `queue_depth{queue}`, `rag_query_duration_seconds`, `cache_hits_total{cache=semantic|prompt}`.

**Dashboards (provisioned as code):** 1) Platform Health (latency, errors, queue depths, pod resources) · 2) LLM Cost & Usage (spend by dept/agent/model, token trends, cache hit rate, budget burn-down) · 3) Agent Quality (success rate, feedback score, eval pass rate, approval override rate, tool-selection errors) · 4) Adoption (WAU, sessions per dept, automations run).

### 6.4 Logs — Loki [CORE]
Structured JSON (`ts, level, service, trace_id, user_hash, event, detail`). PII scrubbed at the logger (Presidio-lite regex layer). Retention: app logs 30d, audit table 2y (DB, not Loki).

### 6.5 Alerting [CORE]
Alertmanager → Slack `#fleet-alerts`: error rate >5%/5m, p95 chat latency >8s/10m, queue depth >100/10m, budget 80%/100%, eval pass-rate drop >10pts on release, provider fallback activated, pod crash-loops.

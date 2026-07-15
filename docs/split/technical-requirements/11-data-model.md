# TRD · Data Model (§11)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 11. Data Model (PostgreSQL — core tables)

```
users(id, kc_sub, email_hash, display_name, dept_id, status)
departments(id, name)
roles/user_roles(user_id, role, dept_id)
api_keys(id, name, hash, scopes[], dept_id, expires_at, created_by)
agents(id, name, dept_id, status, reasoning_model, utility_model,
       sensitivity, guardrail_policy_id, semantic_cache bool,
       semantic_cache_threshold, max_context_tokens)
prompt_versions(id, agent_id, version, content, changelog, created_by, eval_run_id)
agent_tools(agent_id, tool_id) · tools(id, mcp_server, name, description, risk_class)
collections(id, name, dept_id, sensitivity, retention_days, pii_policy)
documents(id, collection_id, uri, sha256, ocr_status, meta jsonb)
chunks(id, document_id, content_sha256, qdrant_point_id, tokens,
       redacted bool, original_sensitivity)  [§8: redacted chunks record both]
conversations(id, agent_id, user_id) · messages(id, conv_id, role, content,
       tool_trace jsonb, tokens_in, tokens_out, cost_usd, trace_id)
approvals(id, agent_id, run_id, action, payload jsonb, status, decided_by, decided_at, sla_at)
models(… see §4.1) · budgets(id, scope_type[global|dept|agent|user], scope_id,
       period, limit_usd, soft_pct) · spend_ledger(id, ts, model, agent_id, user_id,
       dept_id, tok_in, tok_out, tok_cached, cost_usd, trace_id)  [monthly partitions P2]
eval_datasets/eval_runs(id, agent_id, pass_rate, metrics jsonb, git_sha)
audit_log(id, ts, actor, actor_type, action, entity, entity_id, detail jsonb, trace_id) [append-only]
feedback(id, message_id, score, reason)
```

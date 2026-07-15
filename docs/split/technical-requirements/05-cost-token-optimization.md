# TRD · Cost & Token Optimization (§5)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 5. Cost & Token Optimization

| Mechanism | How | Tag |
|---|---|---|
| **Budget hierarchy** | LiteLLM virtual keys per (department, agent). Budgets: global → department → agent → user. Soft limit 80% → Slack+UI warning; hard limit 100% → block with clear error. Admin override with audit entry. | [CORE] |
| **Spend ledger** | Every LLM call logged: tokens in/out/cached, computed cost, agent, user, dept, trace_id → `spend_ledger` (source: LiteLLM spend logs webhook). Powers Cost dashboard. | [CORE] |
| **Model tiering** | utility vs reasoning models per agent (see 4.2). Default for new agents = utility for all helper calls. | [CORE] |
| **Prompt caching** | Anthropic `cache_control` breakpoints on (system prompt, tool schemas, KB context); OpenAI automatic caching honored. Cache hit tokens metered at cached price. | [CORE] |
| **Semantic cache** | Redis: embedding of normalized query, cosine ≥ threshold within same agent+collection scope → serve cached answer with "cached" badge. Threshold is a **per-agent tunable validated against the agent's eval set** (start 0.95; Turkish morphology can embed semantically different questions closely — near-miss fixtures belong in the eval set). Opt-in per agent (only deterministic Q&A agents), TTL default 24h, invalidated on KB collection update. | [CORE] |
| **Context budgeting** | Per-agent `max_context_tokens`. Conversations: rolling window + LLM-generated summary of evicted turns (utility model). RAG: `top_k` + per-chunk token cap + total retrieved-tokens cap. | [CORE] |
| **Embedding dedup** | `content_sha256` on chunks; identical chunk never re-embedded (re-upload of same doc costs ~0). | [CORE] |
| **Batch lane** | Non-interactive jobs (nightly CV batch, bulk listing re-checks) run through provider Batch APIs (~50% cheaper) via `arq` scheduled jobs. | [P2] |
| **Streaming everywhere** | SSE for all chat; improves perceived latency (UX, not cost). | [CORE] |
| **Cost anomaly alerts** | Alertmanager rule: dept daily spend > 3× 7-day average → Slack. | [CORE] |

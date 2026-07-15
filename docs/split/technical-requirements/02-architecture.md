# TRD · High-Level Architecture (§2)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 2. High-Level Architecture

```
                        ┌────────────────────────────────────────────┐
                        │              Web UI (Next.js/TS)           │
                        │ Chat · KB · Agent Builder · Workflows ·    │
                        │ Approvals · Admin (Users/Models/Budgets/   │
                        │ Costs/Audit/Health) · i18n TR/EN           │
                        └───────────────┬────────────────────────────┘
                                        │ HTTPS (OIDC session), SSE
   Keycloak (OIDC) ◄────────────────────┤
                        ┌───────────────▼────────────────────────────┐
                        │        API Gateway (FastAPI, stateless)     │
                        │ AuthZ (RBAC) · rate limit · trace_id ·      │
                        │ audit middleware · budget pre-check         │
                        └──┬─────────────┬─────────────┬─────────────┘
                           │             │             │
              ┌────────────▼──┐   ┌──────▼──────┐  ┌───▼─────────────┐
              │ Agent Runtime │   │ RAG Service │  │ n8n (queue mode)│
              │  (LangGraph,  │   │ ingest/query│  │ main + workers  │
              │  PG checkpts) │   │ workers(arq)│  │ calls Fleet API │
              └──────┬────────┘   └──────┬──────┘  └───┬─────────────┘
                     │ tools             │ embed       │
              ┌──────▼──────────────┐    │        ┌────▼────┐
              │ MCP Servers          │   │        │  Redis  │ queue·cache·
              │ jira│github│slack│   │   │        └─────────┘ ratelimit
              │ email│pg_ro│ocr│int. │   │
              └──────┬──────────────┘    │
                     │                   │
        ┌────────────▼───────────────────▼───────────────────────────┐
        │              LLM Gateway (LiteLLM Proxy, DB-backed)         │
        │ model registry · virtual keys · budgets · fallbacks ·       │
        │ prompt-cache passthrough · spend logs → Langfuse callback   │
        └───────┬──────────────────────┬──────────────────────────────┘
                │ cloud APIs           │ local
        Anthropic/OpenAI/…       Ollama (dev) / vLLM (prod GPU)
                                   [KVKK-restricted traffic]

  Data plane: PostgreSQL16(+pgbouncer) · Qdrant · MinIO(S3) · Redis
  Observability: Langfuse (LLM traces/cost/evals) · Prometheus ·
                 Grafana · Loki · OpenTelemetry · Alertmanager→Slack
```

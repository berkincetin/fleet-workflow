# TRD · Technology Stack (§3)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 3. Technology Stack (Decided)

| Concern | Choice | Why |
|---|---|---|
| API / services | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 async | Typed, async, fast to build |
| Agent orchestration | LangGraph + Postgres checkpointer | Durable multi-step state, native HITL interrupts, resumable after crash |
| LLM gateway | **LiteLLM Proxy** (DB-backed) | 100+ providers behind one OpenAI-compatible API; built-in virtual keys, budgets, spend logs, fallbacks — solves "add any model via API" |
| Local models | Ollama (dev: host-native, NVIDIA GPU) / vLLM (prod, GPU) | KVKK-sensitive traffic stays on-prem; both behind LiteLLM. Dev pattern: Ollama runs on the host with direct GPU access; containers reach it via host gateway — avoids GPU passthrough complexity in k3d/compose. The `make dev PROFILE=ollama` compose profile is only a **containerized fallback** for a machine without a host-native GPU Ollama (CPU, low volume); the host-native GPU path above is the norm and the Sprint 8 hard requirement. |
| LLM observability | **Langfuse (self-hosted)** | Traces, generations, prompt versions, cost, user feedback, eval datasets |
| System observability | OpenTelemetry, Prometheus, Grafana, Loki, Alertmanager | Standard, self-hosted |
| Vector DB | Qdrant | Filters, hybrid search, snapshots, good K8s story |
| RDBMS | PostgreSQL 16 + pgbouncer | App state, checkpoints, audit, spend ledger |
| Cache/queue | Redis 7 (+ arq workers) | Job queue (ingestion, async agent tasks), semantic cache, rate limits |
| Object storage | MinIO (S3 API) | Uploaded docs, OCR artifacts, exports |
| AuthN | **Keycloak** (OIDC) | Same component in demo and prod; federates to corporate SSO (Azure AD/Google) later |
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui | Standard internal-tool stack; i18n (TR/EN) via next-intl |
| Workflows | n8n **queue mode** (main + workers + Redis) | Scales to hundreds of automations. Runs on its own subdomain behind SSO proxy; integrated via API/webhooks (fair-code license ⇒ no white-label embedding) |
| OCR | Vision LLM (primary) + Tesseract `tur` (local fallback) | Layout-aware extraction; local path for sensitive docs |
| PII detection | Microsoft Presidio + custom TR recognizers (TCKN checksum, TR IBAN, TR phone) | KVKK pipeline |
| Deploy | Docker → **one Helm umbrella chart**; k3d locally; GitHub Actions CI/CD | K8s from day one without cloud dependency |
| Load testing | k6 | Scriptable, CI-friendly |
| Security testing | trivy (deps+images), bandit/semgrep (SAST), OWASP ZAP baseline (DAST), garak (LLM probing) | Covers app + LLM attack surface |

# TRD · Scalability & Capacity (§10)

<!-- Derived from docs/TECHNICAL_REQUIREMENTS.md. The original is canonical.
     Any change here must also be applied to docs/TECHNICAL_REQUIREMENTS.md in the same PR. -->

## 10. Scalability & Capacity

- **Stateless services** (gateway, runtime workers, RAG query) → HPA on CPU + custom metric `queue_depth`. Long tasks go through Redis/arq; LangGraph state in Postgres ⇒ pods are disposable mid-run.
- **n8n queue mode:** 1 main + N workers; workflows call Fleet via API keys; concurrency per worker capped; backpressure = queue.
- **DB:** pgbouncer (transaction pooling), indexes defined in migrations, `spend_ledger` and `audit_log` partitioned monthly [P2].
- **Targets (SLO):** chat first token p50 <2s / p95 <6s; RAG e2e p95 <5s; 300 concurrent chat sessions and 200 automation runs/hour on the reference cluster without SLO breach.
- **Reference sizing:**

| Environment | Spec |
|---|---|
| Dev laptop (compose) — **confirmed target** | 8 CPU / 16 GB RAM minimum (full stack + browser is tight at 16 GB; **24 GB recommended**) / 40 GB disk; NVIDIA GPU runs the local-model lane host-native (7B q4 ≈ 5 GB VRAM, 14B q4 ≈ 9 GB) |
| k3d demo (single node) | 8 CPU / 24–32 GB RAM |
| Prod-small (K8s) | 3× (8 vCPU / 32 GB) app nodes + 1 GPU node (L4/A10, 24 GB) for vLLM [GPU optional if PII lane uses CPU Ollama at low volume] |

# Runbook — On-call basics

First responder guide for the Fleet platform. Pair this with
[restore.md](restore.md) (backup/DR) and
[local-lane-ollama-tuning.md](local-lane-ollama-tuning.md).

## 1. Is it up? — health at a glance

| Check | How |
|---|---|
| API liveness / readiness | `GET /healthz` (process), `GET /readyz` (deps: DB/Redis) |
| Pods (k8s) | `kubectl -n <ns> get pods` — all `Running`/`Ready` |
| CNPG Postgres | `kubectl -n <ns> get cluster postgres` → `Cluster in healthy state` |
| Metrics | `GET /metrics` on the API; dashboards in Grafana |
| Traces + cost | Langfuse (per-request trace, tokens, cost) |
| Logs | Loki (structured JSON; PII is scrubbed at the log filter) |

Every request carries a **`trace_id`** (returned as `X-Trace-Id`, emitted in the
audit log and the SSE `done` event). It is the join key across API logs, the
audit table, and the Langfuse trace — start any incident from a trace_id.

## 2. Common symptoms → first moves

**Chat returns no tokens / an `error` SSE event.**
- Check the API log for the failing call. Most common causes:
  - **Gateway/LLM failure** (`GatewayError`): the provider is down or a key is
    missing/invalid. The gateway falls back across providers; if all fail it
    surfaces the error. Verify keys and `GET /health/liveliness` on LiteLLM.
  - **Qdrant `Vector dimension error: expected N, got M`**: a RAG agent's
    collection was ingested with one embedding model and is being queried with
    another (e.g. local `bge-m3` 1024-dim vs cloud `text-embedding-3-small`
    1536-dim). Fix: keep the agent on the lane its collection was ingested with,
    or re-ingest the collection under the new lane.
  - **`checkpoints does not exist`**: LangGraph checkpointer tables were never
    created on a fresh DB. Run `make migrate` (it calls `checkpointer_setup`).

**429 Too Many Requests.** The per-client fixed-window rate limiter tripped
(`FLEET_RATE_LIMIT_PER_MINUTE`, default 120/min per IP). Expected under load
tests; raise the limit only deliberately.

**A budget hard-stop rejects requests.** Spend hit a configured budget
(`/admin/budgets`). Confirm it is intended before raising it — costs are a
feature, not an accident.

**Local lane slow / timing out.** CPU-only or VRAM-starved inference. See
[local-lane-ollama-tuning.md](local-lane-ollama-tuning.md): keep the model
resident (`OLLAMA_KEEP_ALIVE`), ensure the model fits in free VRAM, and prefer
one model per GPU for a sequential workload.

## 3. Stopping a misbehaving agent — kill switch

Agents can be **paused** individually (TRD §9). A paused agent's graph
short-circuits at the killswitch gate before any node runs, and the chat
endpoint returns `409 agent is paused`. Toggle via the admin surface (agent
status) or the KillSwitch (Redis-backed), and confirm with a chat call returning
409. Kill switch also blocks `write:*` tool execution independently of pausing.

## 4. Approvals — nothing external auto-executes

Every `write:external` action goes through the HITL approval queue
(`/approvals`). If external side effects are firing without approval, that is a
guardrail breach, not an operational tuning issue — treat it as an incident and
capture the trace_id.

## 5. Backups & restore

Postgres PITR and Qdrant snapshot restore are in [restore.md](restore.md)
(exercised on a scratch cluster). RPO 24h / RTO 4h (internal-tool tier). WAL
archives continuously to MinIO; base backups nightly; Qdrant snapshots nightly;
MinIO versioning is on.

## 6. Escalation

- Data loss / suspected corruption → follow [restore.md](restore.md), do **not**
  restore in place (CNPG restores into a *new* cluster).
- Guardrail breach (unapproved external write, sensitivity-routing bypass, PII in
  logs/traces) → incident; preserve the trace_id and the audit rows.
- Sustained SLO breach → check the Grafana dashboards and the last k6 report in
  `tests/load/reports/`; scale the relevant lane (LLM gateway / runtime workers)
  per the capacity notes in TRD §10.

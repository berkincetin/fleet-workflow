# Fleet — Internal AI Operations Platform

Governed LangGraph agents, a RAG knowledge base, an MCP tool layer, an LLM
gateway with budgets, full observability (Langfuse + Prometheus/Grafana/Loki),
Keycloak RBAC, and a KVKK-aware local-model lane — Kubernetes-ready from day one.

Two ways to run it: **compose** (the dev stack, used during development) or
**k3d** (a local Kubernetes cluster that mirrors staging/prod via the same Helm
chart).

---

## Prerequisites

- **Docker Desktop** (running)
- **`uv`** (Python 3.12 toolchain), **`pnpm`**, **GNU Make**
- For the k3d path: **`k3d`**, **`kubectl`**, **`helm`**
- Optional local-model lane (cost-free chat, no cloud keys): **Ollama** + a GPU
  (or CPU, slower)

On Windows, `make`/`k3d`/`helm`/`k6`/`gh` install cleanly via `winget`
(`GnuWin32.Make`, `k3d.k3d`, `Helm.Helm`, `GrafanaLabs.k6`, `GitHub.cli`); `uv`
and `pnpm` via their own installers. The Bash examples below run under Git Bash.

---

## Quick start (compose) — running demo in ≤30 min

```bash
uv sync                       # Python venv + workspace + dev deps
pnpm install                  # JS workspace deps
cp .env.example .env          # fill in API keys if you want the cloud lane (see below)

make dev                      # boot the full local stack (~15 services)
make seed-demo                # schema + checkpointer + synthetic data + KB ingest

# two hot-reload dev servers, in separate terminals:
make api                      # FastAPI gateway on :8000
make web                      # Next.js UI on :3000
```

Open **http://localhost:3000**, log in through Keycloak, and you have a running
demo. See **[the demo walkthrough](#demo-walkthrough)** below.

### Model lane: local vs cloud

The gateway (LiteLLM) routes by request sensitivity. Out of the box:

- **Local lane (default for this demo, cost-free):** start Ollama and pull the
  two models the lane uses, then no cloud keys are needed —
  ```bash
  ollama pull qwen2.5:14b-instruct-q4_K_M   # reasoning (~9 GB)
  ollama pull bge-m3                         # embeddings
  ```
  The 14B is the pinned local reasoning model: the Legal Document Review agent
  (`legal_review`) needs it to tell a compliant clause from a violating one, and
  the 7B measurably could not (see `docs/reports/sprint-12.md`). On a machine
  that cannot hold it, swap `local-reasoning` back to
  `qwen2.5:7b-instruct-q4_K_M` in `gateway/litellm/config.yaml` and expect
  `make eval AGENT=legal_review` to fail.
  `make seed-demo` ingests the demo KB with `bge-m3` (1024-dim). Keep RAG agents
  on the local lane so query embeddings match the stored vectors.
- **Cloud lane:** put a real `OPENAI_API_KEY` (and/or `ANTHROPIC_API_KEY`,
  `GEMINI_API_KEY`) in `.env` and restart the gateway
  (`docker compose ... up -d --force-recreate litellm`). If you switch a
  RAG agent to a cloud lane, re-ingest its collections so the stored embedding
  dimension matches the cloud model, otherwise queries fail with a Qdrant
  dimension error.

### Seed logins (synthetic)

| user | password | role |
|---|---|---|
| `admin` | `admin` | platform admin — all screens |
| `builder` | `builder` | agent/model management |
| `approver` | `approver` | approval queue |
| `user1` / `user2` | (same) | member — chat, knowledge |

---

## Service map

| Service | URL | Notes |
|---|---|---|
| Web UI | http://localhost:3000 | Next.js app (login via Keycloak) |
| API | http://localhost:8000 | FastAPI gateway (`/healthz`, `/readyz`) |
| Keycloak | http://localhost:8080 | admin `admin`/`admin`; realm `fleet` |
| Grafana | http://localhost:3001 | `admin`/`admin` — dashboards, metrics |
| n8n | http://localhost:5679 | automation editor |
| MinIO console | http://localhost:9001 | `fleet`/`fleet_dev_pw` — buckets + versioning |
| Mailpit | http://localhost:8025 | captured outbound mail |
| Langfuse | http://localhost:3001 (own port in compose) | LLM traces + cost |

---

## Demo walkthrough

The full 15-minute script lives in
[docs/split/implementation-plan/99-demo-script-and-deferrables.md](docs/split/implementation-plan/99-demo-script-and-deferrables.md).
The platform shows one pattern end to end: **agent → MCP tool → guardrail →
approval → trace**. RAG is one part of it, not the whole thing.

What to click, by capability:

1. **Support Copilot (RAG)** — `/chat`, pick `support_copilot`, ask
   *"What is the Trink sat! process?"* → a streamed, **cited** answer from the
   KB. Thumbs-down a message, then find that trace (with cost) in Langfuse.
2. **Self-service Analytics (text-to-SQL, not RAG)** — `/chat`, pick
   `analytics`, ask *"How many sales are there in total?"* → it generates SQL
   against the read-only fixture tables and answers (500).
3. **Dev Agent (MCP + human-in-the-loop)** — a task that needs a
   `write:external` action lands in **`/approvals`**; approve it there. Nothing
   external auto-executes.
4. **Invoice / HR (document + HITL)** — document → OCR → extraction → approval,
   from the scenario flows under `/scenarios`.
5. **KVKK local lane** — a `pii` request is served entirely by the local model;
   the gateway shows no cloud egress for it.
6. **Admin** — `/admin/{cost,budgets,models,users,audit,api-keys}`: cost
   dashboard, budget limits, the model **clearance** column, audit→trace
   deep-links.

---

## k3d (Kubernetes, mirrors staging/prod)

Same umbrella chart as staging/prod, per-env values. Postgres runs under the
**CloudNativePG** operator with WAL backups to MinIO (see
[docs/runbooks/restore.md](docs/runbooks/restore.md)).

```bash
make k3d-up        # create the cluster, install the CNPG operator + the chart
make k3d-down      # tear it down
```

---

## Common commands

```bash
make dev / make down        # bring the compose stack up / down
make seed-demo              # all demo data in one shot (migrate + seed + KB)
make migrate / make seed    # schema (+ checkpointer) / synthetic data
make n8n-import             # import + activate the n8n workflows (once per fresh stack)
make test                   # unit + integration (testcontainers)
make e2e                    # Playwright against the compose stack
make eval AGENT=x           # golden-set eval (ALL=1 for every agent)
make load TEST=chat_smoke   # k6 load scenario (report in tests/load/reports/)
make scan                   # bandit + gitleaks
make lint                   # ruff + mypy / eslint + tsc
```

---

## Documentation

- **Start here:** [docs/split/INDEX.md](docs/split/INDEX.md) — small part files
  mapping every topic/sprint/scenario (read these, not the large originals).
- Technical requirements, implementation plan, department scenarios, ADRs, and
  runbooks live under [docs/](docs/).
- Per-sprint findings reports: [docs/reports/](docs/reports/).
- Durable progress log: [docs/PROGRESS.md](docs/PROGRESS.md).

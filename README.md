# fleet-workflow
Internal AI operations platform: governed LangGraph agents, RAG knowledge base, MCP tool layer, LLM gateway with budgets, full observability, and a KVKK-aware local-model lane — Kubernetes-ready from day one.

## Dev setup (bootstrap — finalized in task 10.1)

Prerequisites: Docker Desktop, `uv`, `pnpm`, GNU Make.

```bash
uv sync            # create the Python venv and install workspace + dev deps
pnpm install       # install JS workspace deps
make dev           # boot the full local stack (docker compose)
```

The four environments (`local` compose, `test`, `demo/staging`, `prod`) share one Helm
chart with per-env values; only `local` runs during development (see docs/TECHNICAL_REQUIREMENTS.md §14).

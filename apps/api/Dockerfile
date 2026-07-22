# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# Install uv (pinned) for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /bin/

WORKDIR /app

# fleet-api depends on fleet-runtime and (Sprint 5) fleet-mcp via `tool.uv.sources`
# workspace = true; fleet-mcp in turn depends on fleet-rag, which depends back on
# fleet-api (a workspace-metadata cycle uv resolves fine since nothing actually
# imports circularly at module load — see apps/mcp/pyproject.toml). So uv needs
# all four workspace members present to resolve fleet-api's dependency tree, not
# just apps/api/ + apps/runtime/.
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/fleet_api apps/api/fleet_api
COPY apps/runtime/pyproject.toml apps/runtime/pyproject.toml
COPY apps/runtime/core apps/runtime/core
COPY apps/runtime/agents apps/runtime/agents
COPY apps/rag/pyproject.toml apps/rag/pyproject.toml
COPY apps/rag/fleet_rag apps/rag/fleet_rag
COPY apps/mcp/pyproject.toml apps/mcp/pyproject.toml
COPY apps/mcp/fleet_mcp apps/mcp/fleet_mcp
COPY infra/migrations infra/migrations

# Install the api package (+ its fleet-runtime/fleet-rag/fleet-mcp workspace
# dependencies) into a venv.
RUN uv pip install --system --no-cache ./apps/api ./apps/runtime ./apps/rag ./apps/mcp

# Non-root user.
RUN useradd --create-home --uid 10001 fleet
USER fleet

# Placeholder entrypoint — the FastAPI server lands in task 1.3.
CMD ["python", "-c", "import fleet_api; print('fleet-api image OK')"]

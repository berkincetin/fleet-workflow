# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# Install uv (pinned) for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /bin/

WORKDIR /app

# fleet-api depends on fleet-runtime via `tool.uv.sources` workspace = true
# (Sprint 4: agent kill switches/chat routing use core.llm/core.killswitch),
# so uv needs the whole workspace root — not just apps/api/ — to resolve it.
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/fleet_api apps/api/fleet_api
COPY apps/runtime/pyproject.toml apps/runtime/pyproject.toml
COPY apps/runtime/core apps/runtime/core
COPY infra/migrations infra/migrations

# Install the api package (+ its fleet-runtime workspace dependency) into a venv.
RUN uv pip install --system --no-cache ./apps/api ./apps/runtime

# Non-root user.
RUN useradd --create-home --uid 10001 fleet
USER fleet

# Placeholder entrypoint — the FastAPI server lands in task 1.3.
CMD ["python", "-c", "import fleet_api; print('fleet-api image OK')"]

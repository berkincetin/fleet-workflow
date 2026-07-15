# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# Install uv (pinned) for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /bin/

WORKDIR /app

# Copy only the api package's metadata + source (build context is the repo root).
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/fleet_api apps/api/fleet_api
COPY infra/migrations infra/migrations

# Install the api package into a venv.
RUN uv pip install --system --no-cache ./apps/api

# Non-root user.
RUN useradd --create-home --uid 10001 fleet
USER fleet

# Placeholder entrypoint — the FastAPI server lands in task 1.3.
CMD ["python", "-c", "import fleet_api; print('fleet-api image OK')"]

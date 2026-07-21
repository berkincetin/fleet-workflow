COMPOSE := docker compose -f infra/compose/docker-compose.dev.yml

.PHONY: dev down lint test migrate seed scan openapi client helm-lint k3d-up k3d-down gateway-sync gateway-check

dev: ## boot the full local dev stack
	$(COMPOSE) up -d

down: ## stop the dev stack
	$(COMPOSE) down

lint: ## ruff + mypy (Python) and eslint (web); tsc/typecheck wired in when web gains real code
	uv run ruff check .
	-uv run mypy apps packages
	pnpm -r --if-present lint

test: ## unit + integration (testcontainers)
	uv run pytest tests/unit -q
	uv run pytest tests/integration -q

migrate: ## apply DB migrations (alembic upgrade head)
	uv run alembic -c infra/migrations/alembic.ini upgrade head

seed: ## load synthetic data + analytics fixture views
	uv run python -m fleet_api.seed

scan: ## security scans (bandit + gitleaks; trivy in CI)
	-uv run bandit -r apps packages -ll
	-gitleaks detect --no-banner --redact

openapi: ## dump the API OpenAPI schema to packages/shared/openapi.json
	uv run python -m fleet_api.export_openapi packages/shared/openapi.json

client: openapi ## generate the TypeScript client from the OpenAPI schema
	pnpm --filter @fleet/shared install
	pnpm --filter @fleet/shared gen

gateway-sync: ## refresh LiteLLM config prices from the litellm price map
	uv run python gateway/litellm/pricing_sync.py

gateway-check: ## fail if LiteLLM config prices have drifted (CI)
	uv run python gateway/litellm/pricing_sync.py --check

helm-lint: ## lint the umbrella chart
	helm lint infra/helm/fleet -f infra/helm/fleet/values-dev.yaml

k3d-up: ## create a local k3d cluster and install the chart
	bash infra/k3d/up.sh

k3d-down: ## delete the local k3d cluster
	k3d cluster delete fleet

COMPOSE := docker compose -f infra/compose/docker-compose.dev.yml

.PHONY: dev down lint test migrate seed scan

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

COMPOSE := docker compose -f infra/compose/docker-compose.dev.yml

.PHONY: dev down lint test

dev: ## boot the full local dev stack
	$(COMPOSE) up -d

down: ## stop the dev stack
	$(COMPOSE) down

lint: ## ruff + mypy (Python) and eslint + tsc (web)
	uv run ruff check .
	-uv run mypy apps packages
	pnpm -r --if-present lint

test: ## unit + integration (wired up in Stage B)
	uv run pytest tests/unit -q

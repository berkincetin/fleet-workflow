COMPOSE := docker compose --env-file .env -f infra/compose/docker-compose.dev.yml

.PHONY: dev down lint test migrate seed scan openapi client helm-lint k3d-up k3d-down gateway-sync gateway-check api web n8n-import

dev: ## boot the full local dev stack
	$(COMPOSE) up -d

down: ## stop the dev stack
	$(COMPOSE) down

api: ## hot-reload the Fleet API (uvicorn --reload) on :8000
	uv run uvicorn fleet_api.app:create_app --factory --reload --port 8000

web: ## hot-reload the Next.js web shell on :3000
	pnpm --filter web dev

lint: ## ruff + mypy (Python) and eslint (web); tsc/typecheck wired in when web gains real code
	uv run ruff check .
	-uv run mypy apps packages
	pnpm -r --if-present lint

test: ## unit + integration (testcontainers)
	uv run pytest tests/unit -q
	uv run pytest tests/integration -q

migrate: ## apply DB migrations (alembic upgrade head) + LangGraph checkpointer tables
	uv run alembic -c infra/migrations/alembic.ini upgrade head
	uv run python -m fleet_api.checkpointer_setup

seed: ## load synthetic data + analytics fixture views
	uv run python -m fleet_api.seed

seed-docs: ## ingest Support Copilot demo KB docs into cs-help-center/cs-procedures (run after seed)
	uv run python -m fleet_rag.seed_docs

n8n-import: ## import + activate the workflows/*.json exports into n8n (run once per fresh stack, task 6.5.4)
	$(COMPOSE) exec n8n-main n8n import:workflow --separate --input=/import/workflows
	$(COMPOSE) exec n8n-main n8n update:workflow --all --active=true
	$(COMPOSE) restart n8n-main n8n-worker

eval: ## run an agent's eval dataset against the live stack; ALL=1 for every agent (make eval AGENT=support_copilot)
ifdef ALL
	@for a in $$(uv run python -c "import yaml; print(' '.join(yaml.safe_load(open('evals/config.yaml'))['agents']))"); do \
		uv run python evals/runner.py --agent $$a || exit 1; \
	done
else
	uv run python evals/runner.py --agent $(AGENT)
endif

scan: ## security scans (bandit + gitleaks; trivy in CI)
	-uv run bandit -r apps packages -ll
	-gitleaks detect --no-banner --redact

load: ## k6 load scenario (make load TEST=chat_smoke | mixed_day); writes a JSON summary to tests/load/reports/
	@mkdir -p tests/load/reports
	k6 run --summary-export tests/load/reports/$(TEST).json tests/load/$(TEST).js

openapi: ## dump the API OpenAPI schema to packages/shared/openapi.json
	uv run python -m fleet_api.export_openapi packages/shared/openapi.json

client: openapi ## generate the TypeScript client from the OpenAPI schema
	pnpm --filter @fleet/shared install
	pnpm --filter @fleet/shared gen

e2e: ## Playwright E2E vs a running stack — needs `make dev` + `make api` + web built/started in production mode (see tests/e2e/playwright.config.ts)
	pnpm --filter @fleet/e2e install
	pnpm --filter @fleet/e2e exec playwright test

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

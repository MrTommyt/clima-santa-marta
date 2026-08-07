.DEFAULT_GOAL := help
.PHONY: help setup dev down test test-int lint format api clean rebuild openmeteo-plan openmeteo-prefetch metar-plan metar-prefetch check-env

ENV_FILE ?= .env.local
UV_RUN := uv run --env-file $(ENV_FILE)

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Create .env, install the Python workspace and pre-commit hooks
	cp -n .env.example .env || true
	uv sync --all-packages
	uv run pre-commit install

dev: ## Start the local platform and wait until every service is healthy
	docker compose up -d --wait

rebuild: ## Rebuild the custom images (airflow, mlflow) and restart on them
	docker compose build
	docker compose up -d --wait

down: ## Stop the local platform (data volumes are kept)
	docker compose down

test: ## Run unit tests (no docker required)
	uv run pytest -m "not integration and not e2e"

test-int: ## Run integration tests (requires `make dev` to be up)
	uv run pytest -m integration

lint: ## Ruff check, format check, and mypy
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

format: ## Auto-fix lint issues and reformat
	uv run ruff format .
	uv run ruff check --fix .

api: ## Run the FastAPI app locally with reload
	uv run uvicorn clima_api.main:app --reload

clean: ## Stop the platform AND DELETE volumes (needed if the Postgres DB layout changes), drop caches
	docker compose down -v
	rm -rf .venv .ruff_cache .mypy_cache .pytest_cache

check-env:
	$(UV_RUN) python -c \
		'import os; print("MINIO:", os.getenv("MINIO_ENDPOINT")); print("KAFKA:", os.getenv("KAFKA_BOOTSTRAP_SERVERS"))'

openmeteo-plan:
	$(UV_RUN) \
		--package clima-ingestion-openmeteo \
		openmeteo-ingestion \
		--plan

openmeteo-prefetch:
	$(UV_RUN) \
		--package clima-ingestion-openmeteo \
		openmeteo-ingestion

metar-plan:
	$(UV_RUN) \
		--package clima-ingestion-metar \
		metar-ingestion \
		--plan

metar-prefetch:
	$(UV_RUN) \
		--package clima-ingestion-metar \
		metar-ingestion

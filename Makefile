SHELL := /usr/bin/env bash

UV := uv
DOCKER_COMPOSE := docker compose
DBT_PROJECT_DIR ?= transforms
DBT_PROFILES_DIR ?= transforms
PREFECT_API_DATABASE_CONNECTION_URL ?= postgresql+asyncpg://prefect:prefect@localhost:5432/prefect

.DEFAULT_GOAL := help

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: venv
venv: ## Create the local virtual environment.
	$(UV) venv .venv --python 3.12

.PHONY: install
install: venv ## Install all local dependency groups.
	$(UV) sync --all-groups

.PHONY: lint
lint: ## Run Ruff lint checks.
	$(UV) run ruff check .

.PHONY: format
format: ## Format Python files with Ruff.
	$(UV) run ruff format .

.PHONY: format-check
format-check: ## Check Python formatting with Ruff.
	$(UV) run ruff format --check .

.PHONY: typecheck
typecheck: ## Run mypy type checks.
	$(UV) run mypy

.PHONY: test
test: ## Run fast unit tests.
	$(UV) run pytest tests/unit

.PHONY: test-integration
test-integration: db-bootstrap ## Run DB-backed integration tests.
	$(UV) run pytest tests/integration

.PHONY: db-up
db-up: ## Start local Postgres.
	$(DOCKER_COMPOSE) up -d postgres
	@container_id="$$( $(DOCKER_COMPOSE) ps -q postgres )"; \
	for attempt in {1..60}; do \
		status="$$( docker inspect -f '{{.State.Health.Status}}' "$$container_id" )"; \
		if [ "$$status" = "healthy" ]; then \
			echo "Postgres healthy"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	$(DOCKER_COMPOSE) logs postgres; \
	exit 1

.PHONY: db-down
db-down: ## Stop local Postgres without removing its named volume.
	$(DOCKER_COMPOSE) down

.PHONY: db-shell
db-shell: db-up ## Open psql inside the Postgres container.
	$(DOCKER_COMPOSE) exec postgres psql -U felts -d felts

.PHONY: db-check
db-check: db-up ## Verify TimescaleDB and pgvector are enabled.
	@count="$$( $(DOCKER_COMPOSE) exec -T postgres psql -U felts -d felts -tAc "select count(*) from pg_extension where extname in ('timescaledb', 'vector');" )"; \
	test "$$count" = "2"; \
	echo "Postgres extensions ready: timescaledb, vector"

.PHONY: db-bootstrap
db-bootstrap: db-up ## Apply local SQL bootstrap files that may not run on existing volumes.
	$(DOCKER_COMPOSE) exec -T postgres psql -U postgres -d felts < docker/postgres/init/10-create-raw-records.sql

.PHONY: dbt-debug
dbt-debug: db-up ## Verify dbt project/profile and Postgres connectivity.
	@test -f $(DBT_PROFILES_DIR)/profiles.yml || cp $(DBT_PROFILES_DIR)/profiles.yml.example $(DBT_PROFILES_DIR)/profiles.yml
	FELTS_DBT_PROJECT_DIR=$(DBT_PROJECT_DIR) FELTS_DBT_PROFILES_DIR=$(DBT_PROFILES_DIR) \
		$(UV) run dbt debug --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

.PHONY: prefect-check
prefect-check: ## Verify Prefect and project config load.
	PREFECT_API_DATABASE_CONNECTION_URL=$(PREFECT_API_DATABASE_CONNECTION_URL) $(UV) run prefect version
	$(UV) run python -c "from felts.config import get_settings; s = get_settings(); print(f'Prefect API: {s.prefect_api_url}'); print(f'Prefect DB: {s.prefect_api_database_connection_url}')"

.PHONY: prefect-server
prefect-server: db-up ## Start a local Prefect server backed by Dockerized Postgres.
	PREFECT_API_DATABASE_CONNECTION_URL=$(PREFECT_API_DATABASE_CONNECTION_URL) \
		$(UV) run prefect server start --host 0.0.0.0

.PHONY: check
check: lint format-check typecheck test db-check test-integration dbt-debug prefect-check ## Run scaffold verification.

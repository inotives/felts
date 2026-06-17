# Felts

Felts stands for Financial ELT Stacks. This repository is a monorepo-ready Python project for financial data extraction, loading, orchestration, and dbt transformations.

## Local Setup

Install Python 3.12 and `uv`, then run:

```bash
make install
```

Optional local environment setup:

```bash
cp .env.example .env
```

Run the Phase 00 scaffold checks:

```bash
make check
```

`make check` starts Dockerized Postgres, verifies TimescaleDB and `pgvector`, checks the dbt shell, validates the Prefect install/config, runs Ruff, and executes unit smoke tests.

## Common Commands

```bash
make lint
make format
make test
make db-up
make db-shell
make dbt-debug
make prefect-check
make prefect-server
```

`make prefect-server` uses the local Dockerized Postgres database for Prefect metadata instead of SQLite.

# Felts

Felts stands for **Financial ELT Stacks**. It is a Python, dbt, Postgres, and Prefect project for extracting financial data, landing it as raw evidence, and transforming it into source-owned analytical models.

## Current Shape

- Python 3.12 project managed with `uv`
- Dockerized Postgres with TimescaleDB and pgvector
- dbt project under `transforms/`
- Prefect orchestration backed by Postgres
- Feature-based source layout under `src/felts/sources/<source>/`
- Source-owned schemas, for example `coingecko.raw_coins_list` and `coingecko.stg_coingecko__coins_list`
- Non-secret defaults in `config.yaml`
- Secrets and local overrides in `.env`

## Local Setup

Install Python 3.12, `uv`, and Docker, then run:

```bash
make install
cp .env.example .env
```

Set `COINGECKO_API_KEY` in `.env` if you want authenticated CoinGecko demo API calls.

Run the full local check:

```bash
make check
```

This runs linting, formatting checks, mypy, unit tests, Dockerized Postgres checks, integration tests, dbt debug, and Prefect config checks.

## Configuration

Project defaults live in:

```text
config.yaml
```

Local secrets and machine-specific settings live in:

```text
.env
```

Settings precedence is:

```text
explicit args > environment variables > .env > config.yaml > code defaults
```

## Common Commands

```bash
make lint
make format
make typecheck
make test
make test-integration
make check
```

Database:

```bash
make db-up
make db-check
make db-bootstrap
make db-shell
make db-down
```

dbt:

```bash
make dbt-debug
make dbt-run
make dbt-test
```

Prefect:

```bash
make prefect-check
make prefect-server
make prefect-worker
make prefect-register
```

CoinGecko:

```bash
make coingecko-run
make coingecko-smoke
make coingecko-transform
```

## CoinGecko Source

CoinGecko is the first completed source vertical slice. It supports:

- `coins_list`
- `asset_platforms_list`
- `global`
- `global_defi`
- `coins_markets`

Raw data lands into one table per entity under the provider schema:

```text
coingecko.raw_coins_list
coingecko.raw_asset_platforms_list
coingecko.raw_global
coingecko.raw_global_defi
coingecko.raw_coins_markets
```

dbt models for the same provider stay in the same schema with layer prefixes:

```text
coingecko.stg_coingecko__coins_list
coingecko.int_...
coingecko.mart_...
```

## Prefect Orchestration

Phase 04 added Prefect orchestration:

- entity-scoped source deployments
- raw completion events
- downstream dbt transform deployment
- manual master flow
- unscheduled deployment support for manual sources

Start the local Prefect server:

```bash
make prefect-server
```

Open the UI:

```text
http://127.0.0.1:4200
```

In another terminal, start a worker:

```bash
make prefect-worker
```

Register deployments and automations:

```bash
make prefect-register
```

## CSV Import Direction

Phase 05 is being designed around CSV import only. The first planned CSV contracts are:

- OHLCV data from `data/ohlcv/`
- FRED series data from `data/fred/`

Local CSV files under `data/` are runtime inputs and are gitignored. Tests should use small committed fixtures under:

```text
tests/fixtures/csv_import/
```

CSV dataset contracts will be YAML-driven under:

```text
src/felts/sources/csv_import/contracts.yaml
```

The extractor should remain generic. Dataset-specific parameters such as delimiter, encoding, required headers, identity strategy, source record identity fields, and dbt selector belong in YAML.

## Documentation

Key docs:

- [Project spec](docs/project_specs.md)
- [Implementation phases](docs/implementation_phases.md)
- [Raw landing ADR](docs/adr/0001-raw-landing-design.md)
- [Provider schema transform layout ADR](docs/adr/0002-provider-schema-transform-layout.md)
- [YAML-driven CSV contracts ADR](docs/adr/0003-yaml-driven-csv-import-contracts.md)

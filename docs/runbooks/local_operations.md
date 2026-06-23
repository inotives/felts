# Local Operations Runbook

This runbook covers the local Docker operating path for Felts.

## Environment Files

Copy the local template and edit values only when your local setup differs:

```bash
cp settings/.env.local.example settings/.env.local
```

`FELTS_ENV` defaults to `local`, so `settings/.env.local` is loaded when no environment is selected. Use `FELTS_ENV=dev` or `FELTS_ENV=prod` only when running against those environments.

## Local Stack

Start and bootstrap Postgres:

```bash
make db-bootstrap
```

Stop local services without deleting the database volume:

```bash
make db-down
```

## Fast Checks

Run the checks expected in CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest tests/unit
```

## Local DB Acceptance Checks

Run DB-backed tests locally when changing loaders, raw tables, or dbt models:

```bash
make db-bootstrap
uv run pytest tests/integration
```

## CSV Import Smoke

Run the local CSV imports with runtime files under `data/`:

```bash
uv run felts csv import --contract ohlcv --input-uri data/ohlcv/crypto-ohlcv-bitcoin-20260621.csv
uv run felts csv import --contract fred_series --input-uri data/fred/us_cpi-202605.csv
```

Run a bounded CSV backfill by adding date bounds:

```bash
uv run felts csv import --contract fred_series --input-uri data/fred/us_cpi-202605.csv --start-date 2026-05-01 --end-date 2026-05-31
```

## dbt

Run and test the current dbt project locally:

```bash
make dbt-run
make dbt-test
```

For scoped CSV checks:

```bash
uv run dbt run --project-dir transforms --profiles-dir transforms --select stg_csv_import__ohlcv stg_csv_import__fred_series
uv run dbt test --project-dir transforms --profiles-dir transforms --select stg_csv_import__ohlcv stg_csv_import__fred_series
```

## Prefect Registration

Start a local Prefect server:

```bash
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@localhost:5432/prefect uv run prefect server start --host 0.0.0.0
```

Start a worker in another shell:

```bash
PREFECT_API_URL=http://127.0.0.1:4200/api PREFECT_CLIENT_CSRF_SUPPORT_ENABLED=false uv run prefect worker start --pool local --work-queue default
```

Register deployments and event triggers after source, dbt, deployment, or automation changes:

```bash
PREFECT_API_URL=http://127.0.0.1:4200/api PREFECT_CLIENT_CSRF_SUPPORT_ENABLED=false uv run python -m felts.schedules.orchestrator
```

Verify the expected deployments:

```bash
PREFECT_API_URL=http://127.0.0.1:4200/api uv run prefect deployment ls
```

## Raw-to-dbt Verification

Trigger a CSV source deployment:

```bash
PREFECT_API_URL=http://127.0.0.1:4200/api uv run prefect deployment run "csv-import-source/csv-import-fred-series-source" --param input_uri=data/fred/us_cpi-202605.csv
```

A successful source run that inserts valid rows emits a Raw Completion Event. That event should trigger `dbt-transform` with the contract selector.

Check recent flow runs:

```bash
PREFECT_API_URL=http://127.0.0.1:4200/api uv run prefect flow-run ls --limit 10
```

## Query Checks

Query raw and modeled row counts:

```bash
docker compose exec -T postgres psql -U felts -d felts -tAc "select count(*) from csv_import.raw_fred_series;"
docker compose exec -T postgres psql -U felts -d felts -tAc "select count(*) from csv_import.stg_csv_import__fred_series;"
```

## Common Failure Checks

- If a source deployment completes but dbt does not run, re-register deployments and event triggers.
- If CSV imports fail before load, check the YAML contract headers and delimiter.
- If dbt tests fail, inspect the failing model and raw payloads before changing extractor logic.
- If local settings look wrong, confirm `FELTS_ENV` and the matching `settings/.env.<env>` file.

# Felts

Felts stands for **Financial ELT Stacks**. It extracts financial data from APIs
and CSV files, preserves raw evidence in Postgres, transforms it with dbt, and
orchestrates operational runs with Prefect.

Implemented through Phase 06:

- CoinGecko REST ingestion.
- YAML-driven OHLCV and FRED CSV imports.
- Deterministic, idempotent raw landing in Postgres and TimescaleDB.
- dbt staging and CoinGecko mart models.
- Prefect schedules, Raw Completion Events, and scoped dbt transforms.
- Bounded CSV backfills.
- Local, dev, and production environment-file conventions.
- Ruff, mypy, pytest, integration tests, and local operating instructions.

Postgres is currently the only warehouse target. Modeled data is consumed through
direct SQL queries; visualization is deferred.

## Pipeline

```text
API or CSV
  -> ExtractedRecord
  -> RawWriter validation
  -> <source>.raw_<entity>
  -> Prefect Raw Completion Event
  -> dbt staging and marts
  -> SQL query
```

Examples:

```text
coingecko.raw_coins_list
coingecko.stg_coingecko__coins_list
coingecko.mart_coingecko__coins

csv_import.raw_fred_series
csv_import.stg_csv_import__fred_series
```

## Requirements

- Python 3.12
- `uv`
- Docker with Compose

For a one-command Linux Mint deployment after cloning:

```bash
bash scripts/deploy-linux-mint.sh
```

See [Linux production deployment](docs/linux_production_deployment.md).

## Local Setup

```bash
make install
cp settings/.env.local.example settings/.env.local
make db-bootstrap
```

`FELTS_ENV` defaults to `local`. Set `COINGECKO_API_KEY` in
`settings/.env.local` for authenticated CoinGecko demo API calls.

Run the fast checks:

```bash
make lint
make format-check
make typecheck
make test
```

Run DB-backed checks:

```bash
make test-integration
make dbt-debug
```

`make check` runs the full local verification path.

## CoinGecko

Supported entities:

- `coins_list`
- `asset_platforms_list`
- `global`
- `global_defi`
- `coins_markets`

Run all entities:

```bash
uv run felts coingecko run
```

Run selected entities:

```bash
uv run felts coingecko run --entities coins_list global
```

Load and transform CoinGecko data:

```bash
make coingecko-transform
```

## CSV Import

CSV behavior is defined in
`src/felts/sources/csv_import/contracts.yaml`.

Implemented contracts:

- `ohlcv`: semicolon-delimited crypto OHLCV files.
- `fred_series`: FRED observation files.

Runtime CSV files belong under `data/` and are not committed.

```bash
uv run felts csv import \
  --contract ohlcv \
  --input-uri data/ohlcv/crypto-ohlcv-bitcoin-20260621.csv

uv run felts csv import \
  --contract fred_series \
  --input-uri data/fred/us_cpi-202605.csv
```

Run an inclusive bounded backfill:

```bash
uv run felts csv import \
  --contract fred_series \
  --input-uri data/fred/us_cpi-202605.csv \
  --start-date 2026-05-01 \
  --end-date 2026-05-31
```

## dbt

```bash
make dbt-run
make dbt-test
```

Implemented transforms include:

- CoinGecko staging models for all five entities.
- CoinGecko coins and asset-platform marts.
- OHLCV and FRED CSV staging models.

## Prefect

Start the server and worker in separate terminals:

```bash
make prefect-server
```

```bash
make prefect-worker
```

Register the work pool, deployments, and automations:

```bash
make prefect-register
```

The Prefect UI is available at:

```text
http://127.0.0.1:4200
```

Re-run `make prefect-register` after changing source deployments, dbt selectors,
or event automations.

## Configuration

Non-secret defaults live in `config.yaml`. Environment-specific secrets and
overrides live under `settings/`:

```text
settings/.env.local
settings/.env.dev
settings/.env.prod
```

Create them from the committed `.example` templates. Real environment files are
not committed.

Settings precedence:

```text
explicit values
  > process environment
  > settings/.env.<FELTS_ENV>
  > config.yaml
  > file secrets
```

## Common Commands

```bash
make db-up
make db-bootstrap
make db-shell
make db-down

make lint
make format-check
make typecheck
make test
make test-integration

make dbt-debug
make dbt-run
make dbt-test

make prefect-check
make prefect-server
make prefect-worker
make prefect-register
```

## Documentation

- [Project specification](docs/project_specs.md)
- [Implementation phases](docs/implementation_phases.md)
- [Local operations runbook](docs/runbooks/local_operations.md)
- [Linux production deployment](docs/linux_production_deployment.md)
- [Domain glossary](CONTEXT.md)
- [Architecture decisions](docs/adr/)

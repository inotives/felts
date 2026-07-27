# Felts

Felts stands for **Financial ELT Stacks**. It extracts financial data from APIs
and CSV files, preserves raw evidence in Postgres, transforms it with dbt, and
orchestrates operational runs with Prefect.

Implemented through Phase 15:

- CoinGecko REST ingestion.
- Scheduled CoinGecko OHLC candle capture for mapped internal crypto assets.
- Public-compatible CoinGecko OHLC capture using 30-day requests with provider
  4-hour candle staging.
- Phase 15 dbt-derived daily CoinGecko OHLC rollups and daily OHLCV marts built
  from rollup OHLC plus market-chart metrics.
- Alpha Vantage daily time-series ingestion.
- YAML-driven OHLCV and FRED CSV imports.
- Agent-pipe SQLite raw imports.
- Deterministic, idempotent raw landing in Postgres and TimescaleDB.
- dbt staging plus source-owned CoinGecko, Alpha Vantage, and CSV mart models.
- Felts-owned internal asset, asset platform, and provider mapping marts.
- Mart-first MCP analytical access through a schema-qualified allowlist.
- Prefect schedules, Raw Completion Events, and scoped dbt transforms.
- Bounded CSV backfills.
- Local, dev, and production environment-file conventions.
- Ruff, mypy, pytest, integration tests, and local operating instructions.

Postgres is currently the only warehouse target. Modeled data is consumed through
direct SQL queries; visualization is deferred.
Production MCP access is limited to the committed mart-first schema-qualified
allowlist in `settings/felts-prod-data-views.txt`, reconciled with
`scripts/update-prod-data-access.sh`.

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
coingecko.raw_coins_ohlc
coingecko.raw_coins_market_chart
coingecko.stg_coingecko__coins_list
coingecko.stg_coingecko__coins_ohlc
coingecko.stg_coingecko__coins_market_chart
coingecko.mart_coingecko__coins
coingecko.mart_coingecko__coin_ohlc_candles
coingecko.mart_coingecko__coin_daily_market_metrics
coingecko.mart_coingecko__coin_ohlcv_daily

csv_import.raw_fred_series
alphavantage.raw_time_series_daily
agent_pipe.raw_<entity>
csv_import.stg_csv_import__fred_series
alphavantage.mart_alphavantage__daily_prices
csv_import.mart_csv_import__ohlcv
csv_import.mart_csv_import__fred_observations
felts.mart_felts__assets
felts.mart_felts__asset_platforms
felts.mart_felts__asset_provider_mappings
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
- `coins_ohlc`
- `coins_market_chart`

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

- CoinGecko staging models for all seven entities, including provider 4-hour OHLC candles and daily market metrics.
- CoinGecko intermediate daily OHLC rollup models derived from corrected public OHLC capture.
- CoinGecko coins, asset-platform, daily OHLC rollup candle, daily-market-metrics, OHLCV, market-snapshot, global-market, and global-DeFi marts.
- Alpha Vantage daily-price marts.
- OHLCV and FRED CSV staging models.
- OHLCV and FRED CSV marts.
- Felts internal asset, asset-platform, and asset-provider-mapping marts.

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

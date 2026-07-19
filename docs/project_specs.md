# Felts Project Specifications

**Version:** 2.0.0
**Last Updated:** 2026-07-19
**Status:** Implemented through Phase 10

Felts is a financial ELT system that extracts source data, preserves raw evidence in
Postgres, transforms it with dbt, and orchestrates operational runs with Prefect.

This document describes the current implementation. Completed phase documents under
`docs/_archived/` preserve the detailed decisions and acceptance criteria that produced
it.

## 1. Implemented Scope

Phases 01 through 10 delivered:

- Shared extraction, validation, writing, loading, and source-run contracts.
- Postgres and TimescaleDB raw landing with deterministic idempotency.
- A complete CoinGecko REST ingestion path.
- Alpha Vantage daily time-series ingestion.
- dbt source, staging, and mart models.
- Prefect source deployments, Raw Completion Events, and scoped dbt transforms.
- YAML-driven local CSV imports for OHLCV and FRED series data.
- Bounded CSV backfills.
- Environment-specific settings files.
- Constrained production analytical data access through the Felts MCP server.
- Agent-pipe SQLite raw ingestion.
- Fast CI, DB-backed integration checks, and a local operations runbook.

The working pipeline is:

```text
API, CSV, or agent-pipe SQLite
  -> ExtractedRecord
  -> RawWriter validation and RawRecord construction
  -> Postgres raw source schema
  -> Raw Completion Event
  -> dbt staging and downstream models
  -> direct SQL queries
```

Visualization is not implemented. Querying modeled tables directly is the current
consumption path.

## 2. Project Language

`CONTEXT.md` is the canonical glossary. Important boundaries are:

- **Source:** named external or local origin of financial data.
- **Entity:** named kind of data emitted by a Source.
- **ExtractedRecord:** source-shaped record before raw wrapping.
- **RawRecord:** immutable landing record with ingestion and validation metadata.
- **Writer:** validates ExtractedRecords and constructs RawRecords.
- **Loader:** persists RawRecords.
- **Source Run:** one invocation for selected entities of a Source.
- **Entity Run:** one entity processed within a Source Run.
- **Backfill:** bounded replay over an explicit date range.
- **Raw Completion Event:** signal emitted after an Entity Run satisfies its
  source-specific completion condition.

## 3. Runtime and Tooling

| Concern | Current implementation |
|---|---|
| Language | Python 3.12 |
| Dependency and command runner | `uv` |
| Validation and settings | Pydantic v2 and `pydantic-settings` |
| HTTP | `httpx` |
| Postgres driver | synchronous `psycopg` |
| Local warehouse | Dockerized Postgres with TimescaleDB and pgvector |
| Transformation | dbt Core with `dbt-postgres` |
| Orchestration | Prefect 3 |
| Lint and format | Ruff |
| Type checking | mypy |
| Testing | pytest |

Postgres is the only implemented warehouse loader.

## 4. Core Contracts

### 4.1 ExtractedRecord

An extractor emits one `ExtractedRecord` per source payload object. The contract
contains:

- Normalized `source` and `entity` identifiers.
- JSON-object `payload`.
- Required timezone-aware `extracted_at`.
- Optional timezone-aware `observed_at`.
- Optional stable `source_record_id`.
- Optional caller-provided `batch_id`.

Extractors preserve source payload values after the minimum adaptation required to
produce a JSON object.

### 4.2 Schema Registry

`SchemaRegistry` maps `source + entity` to:

- A Pydantic validation model.
- A schema name.
- A string schema version.

Validation is optional. Records without a registered schema may still land. Duplicate
registration for the same `source + entity` is rejected.

### 4.3 RawWriter

`RawWriter.write()` accepts an iterable of mixed ExtractedRecords and:

1. Resolves one batch ID for the write call.
2. Validates each payload when a schema is registered.
3. Normalizes validation errors.
4. Generates a deterministic raw record ID.
5. Constructs RawRecords without discarding invalid payloads.
6. Sends records to the Loader in configurable chunks.
7. Returns a `WriteResult`.

`WriteResult` reports:

- Received, valid, invalid, loaded, skipped, and failed counts.
- The effective batch ID.
- Typed validation or loading errors.

Record identity is stable across JSON key ordering and does not change only because
`batch_id` or ingestion time changed when stronger source identity is available.

### 4.4 Loader

The Loader receives RawRecords and returns a persistence-focused `LoadResult`.
`create_loader()` currently supports only `postgres`.

The Postgres loader:

- Uses one transaction per loader batch.
- Groups mixed records by source schema and entity table.
- Creates missing raw tables and indexes.
- Uses deterministic IDs and `ON CONFLICT DO NOTHING` semantics.
- Reports inserted, skipped duplicate, and failed counts.

## 5. Raw Landing

Raw records land in source-owned schemas:

```text
<source>.raw_<entity>
```

Examples:

```text
coingecko.raw_coins_list
coingecko.raw_global
csv_import.raw_ohlcv
csv_import.raw_fred_series
```

Each raw table contains:

| Column | Purpose |
|---|---|
| `id` | Deterministic raw record identity |
| `source` | Source identifier |
| `entity` | Entity identifier |
| `source_record_id` | Stable source identity when available |
| `observed_at` | Source observation timestamp when available |
| `extracted_at` | Extraction timestamp and hypertable time column |
| `loaded_at` | Database load timestamp |
| `batch_id` | Writer batch identity |
| `schema_name` | Registered validation schema |
| `schema_version` | Registered schema version |
| `is_valid` | Validation outcome |
| `validation_errors` | Normalized validation details |
| `payload` | Preserved JSON source payload |

Raw entity tables are TimescaleDB hypertables on `extracted_at`. The shared
`raw.raw_record_keys` table provides id-only uniqueness before inserting into a
hypertable.

Invalid API or CSV records may land with `is_valid = false`; downstream dbt models
select valid rows.

## 6. CoinGecko Source

CoinGecko is the implemented REST source and supports:

| Entity | Endpoint | Scheduled |
|---|---|---|
| `coins_list` | `/coins/list` | Daily at 00:00 UTC |
| `asset_platforms_list` | `/asset_platforms` | Daily at 00:15 UTC |
| `global` | `/global` | Hourly at minute 00 |
| `global_defi` | `/global/decentralized_finance_defi` | Hourly at minute 15 |
| `coins_markets` | `/coins/markets` | Manual |

The shared REST client provides:

- Configurable base URL and request timeout.
- Retry handling for transient failures.
- Optional CoinGecko demo API key header.
- Pagination support used by market data extraction.

The plain Python runner can process all or selected entities and returns a
`SourceRunSummary`. The CLI and Prefect flows call the same runner.

## 7. CSV Import Source

CSV imports are driven by `src/felts/sources/csv_import/contracts.yaml`. A contract
defines:

- Source and entity.
- Encoding and delimiter.
- Required-header policy.
- Dataset identity strategy.
- Source-record identity fields.
- Observation timestamp column.
- Scoped dbt selector.

Implemented contracts:

| Contract | Input shape | Identity |
|---|---|---|
| `ohlcv` | Semicolon-delimited crypto OHLCV file | Asset and date from filename plus timestamp and row |
| `fred_series` | Standard FRED observation CSV | Value-column header plus observation date |

The CSV extractor:

- Supports local paths and `file://` URIs.
- Rejects HTTP and object-store URIs.
- Validates headers before row extraction.
- Preserves row values as strings in raw payloads.
- Adds `_felts` metadata containing contract, input URI, row number, and identity.
- Marks rows invalid when required observation or identity values are missing.
- Supports inclusive `start_date` and `end_date` filtering.

Each contract has:

- An unscheduled normal Prefect deployment.
- An unscheduled backfill deployment.
- A Raw Completion Event automation using the contract's dbt selector.

Runtime CSV files under `data/` are intentionally not committed.

## 8. dbt Transform Layer

dbt reads valid raw records from source schemas and materializes transformed models in
the same source-owned schema.

Implemented CoinGecko staging models:

- `stg_coingecko__coins_list`
- `stg_coingecko__asset_platforms_list`
- `stg_coingecko__global`
- `stg_coingecko__global_defi`
- `stg_coingecko__coins_markets`

Implemented CoinGecko marts:

- `mart_coingecko__coins`
- `mart_coingecko__asset_platforms`

Implemented CSV staging models:

- `stg_csv_import__ohlcv`
- `stg_csv_import__fred_series`

Staging models:

- Unpack JSON payloads.
- Cast fields to declared analytical types.
- Filter invalid raw rows.
- Deduplicate using each model's declared grain and ordering rules.

dbt model tests enforce required fields and uniqueness where defined. There are no CSV
mart models yet.

## 9. Prefect Orchestration

Source-specific extraction and loading remain in each source package. Shared Prefect
code contains only reusable transform and registration behavior.

Operational behavior:

1. A source deployment runs one entity or CSV contract.
2. The source runner extracts, validates, and loads records.
3. A successful CoinGecko Entity Run that inserts rows emits a Raw Completion Event.
   CSV additionally requires at least one valid inserted row.
4. A Prefect automation starts `dbt-transform` with the entity or contract selector.
5. `dbt-transform` runs `dbt run`, then `dbt test` by default.

Source flows retry twice with a 60-second delay. The shared dbt transform flow retries
once with a 30-second delay.

`python -m felts.schedules.orchestrator` registers:

- The configured work pool.
- CoinGecko deployments.
- CSV normal and backfill deployments.
- The dbt transform deployment.
- Source event-to-transform automations.
- Basic failure handling.

Deployments and automations must be re-registered after relevant source, dbt,
deployment, or automation changes. Exact commands are documented in
`docs/runbooks/local_operations.md`.

## 10. Configuration

Settings precedence is:

1. Explicit constructor values.
2. Process environment variables.
3. `settings/.env.<FELTS_ENV>`.
4. `config.yaml`.
5. File secrets.

`FELTS_ENV` defaults to `local`, loading:

```text
settings/.env.local
```

Supported environment conventions are:

```text
settings/.env.local
settings/.env.dev
settings/.env.prod
```

Committed templates are:

```text
settings/.env.local.example
settings/.env.dev.example
settings/.env.prod.example
```

Real environment files are not committed. Settings cover Postgres, Prefect, dbt,
raw-table naming, loader batch size, and CoinGecko options.

## 11. Operations and Verification

The local operations runbook is `docs/runbooks/local_operations.md`.

Fast CI runs on pull requests and pushes to `main`:

```text
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest tests/unit
```

Database-backed checks remain local:

```text
make db-bootstrap
make test-integration
make dbt-run
make dbt-test
```

Additional local commands cover:

- Postgres startup, health checks, shell access, and shutdown.
- CoinGecko live smoke ingestion.
- Prefect server, worker, registration, and deployment execution.
- Direct SQL checks of raw and modeled tables.

Operational evidence currently comes from CI, Prefect run history, raw tables, dbt
results, and direct SQL queries. A dedicated monitoring or visualization application
is not yet part of the system.

## 12. Current Boundaries

The following are deliberately not implemented:

- CoinMarketCap and DeFi Llama sources.
- BigQuery, Snowflake, or ClickHouse loaders.
- Simultaneous multi-target writes.
- WebSocket or Kafka streaming.
- Automatic schema migration or drift remediation.
- Object-store, SFTP, compressed, or multi-file CSV ingestion.
- CSV upload UI or processed-file tracking.
- A separate backfill raw schema.
- A database-backed CI job.
- Grafana or another visualization application.

## 13. Future Implementation

These capabilities require a concrete business or operational driver and a dedicated
implementation phase before coding begins:

- **Streaming and real-time ingestion:** identify the source, required latency, and
  transformation cadence before choosing Prefect micro-batches or a stream processor.
- **Multi-target fan-out:** define simultaneous-write requirements and partial-failure
  behavior before changing the Writer.
- **Additional warehouse targets:** select BigQuery, Snowflake, or ClickHouse for a
  concrete workload, then prove raw landing and dbt compatibility with live tests.
- **Automated schema versioning and migration:** define a real schema transition and
  how staging models read old and new versions before automating drift handling.
- **Advanced CSV import experience:** define the ingestion interface and file lifecycle
  before adding web UI, SFTP, or object-store event triggers.
- **Visualization:** define the first operational or analytical dashboard before adding
  Grafana as another containerized monorepo application.

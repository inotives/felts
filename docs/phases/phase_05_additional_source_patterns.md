# Phase 05 - Additional Source Patterns

## Goal

Expand Felts from REST ingestion into CSV file ingestion by proving multiple local CSV dataset contracts while preserving the feature-based source structure.

## Core Functionality

- CSV import source using file extraction.
- OHLCV and FRED series CSV schemas defined by CSV import source/extractor contracts.
- Per-dataset metadata extraction rules for values such as asset identity.
- YAML-defined CSV dataset contracts for Phase 05.
- Shared CSV extraction helpers for local files, `file://` URIs, delimiter handling, header validation, and file batching.
- Standard CSV quoting and escaping handled by a real CSV parser.

## Scope

- Implement `src/felts/sources/csv_import/`.
- Add `src/felts/sources/csv_import/contracts.yaml` as the CSV dataset registry.
- Keep the CSV contracts registry path feature-local and fixed for Phase 05.
- Create `src/felts/core/extractors/csv.py`.
- Change the Python console script from `felts.sources.coingecko.cli:main` to `felts.cli:main`.
- Keep source-specific CLI command registration inside source feature folders.
- Use local files from `data/ohlcv/` and `data/fred/` for the first CSV vertical slices.
- Do not impose an `inbound/processed/rejected` data folder structure in Phase 05.
- Do not commit local `data/` CSV files. Commit only small deterministic test fixtures under `tests/fixtures/csv_import/`.
- Require an `input_uri` parameter. Phase 05 only supports local paths and `file://` URIs.
- Allow local absolute paths, repo-relative paths, and `file://` URIs.
- Run one CSV contract per flow run.
- Import one CSV file per flow or CLI run.
- Register one unscheduled Prefect deployment per CSV contract.
- Treat each YAML contract key as the stable user-facing contract ID used by CLI and Prefect parameters.
- Use row-level idempotency for re-imports based on each contract's `raw_record.source_record_id` fields.
- Fail the run before loading any rows when CSV headers do not satisfy the selected contract.
- Add a CLI entry path for local CSV import runs.
- Refactor the `felts` CLI entrypoint into a top-level router so multiple source features can register commands.
- Preserve CSV row values mostly as strings in raw payloads and do typed conversion in dbt staging.
- Add per-row CSV trace metadata under a reserved `_felts` payload key.
- Store `row_number` as the physical file line number, so the first data row after a header is line 2.
- Preserve row-level value problems as invalid raw rows with validation errors when the extractor can detect them.
- Emit raw completion events only when at least one valid raw row is inserted.
- Use the existing raw completion event convention for CSV imports.
- Reuse the existing source/entity run summary shape for CSV imports.
- Support the OHLCV sample format:
  - file example: `data/ohlcv/crypto-ohlcv-bitcoin-20260528.csv`
  - delimiter: semicolon (`;`)
  - encoding: UTF-8 with possible BOM
  - asset identity: derived from the filename for this specific dataset
  - headers: `timeOpen`, `timeClose`, `timeHigh`, `timeLow`, `name`, `open`, `high`, `low`, `close`, `volume`, `marketCap`, `circulatingSupply`, `timestamp`
- Support the FRED series sample format:
  - file example: `data/fred/us_cpi-202605.csv`
  - delimiter: comma (`,`)
  - encoding: UTF-8
  - series identity: derived from the value column header and/or filename for this specific dataset
  - headers: `observation_date`, plus one FRED series id value column such as `CORESTICKM159SFRBATL`
- Keep identity extraction configurable per CSV dataset contract. Some future CSV imports may derive identity from filename patterns, while others may derive it from one or more columns or explicit flow parameters.
- Define Phase 05 CSV dataset contracts in YAML so new CSV imports can be added without changing extractor code when the import behavior is covered by existing generic strategies.
- Keep the CSV extractor generic. Source/entity names, paths, delimiter, encoding, required headers, identity extraction, and field mappings come from YAML.
- Use Python's standard library `csv` module for Phase 05 extraction; do not manually split rows by delimiter and do not use pandas for raw CSV ingestion.
- Include the dbt selector in each CSV contract so successful imports can trigger the right downstream transform.
- Support `filename_pattern` and `value_column_header` identity strategies in Phase 05.
- Add raw and staging models needed to prove the CSV ingestion pattern. Do not add CSV marts in Phase 05.
- Add `flow.py`, `events.py`, `deployments.py`, and `automations.py` inside `src/felts/sources/csv_import/` after the local CSV source works.
- CSV import deployments have no schedules in Phase 05 and are triggered manually with parameters.
- Live/local smoke tests use the two sample CSV files and verify re-import idempotency.
- Prefect live testing runs after the CLI/local runner passes.

## Acceptance Criteria

- CSV import follows the same self-contained source folder pattern.
- CSV extraction reuses core abstractions without source-specific core changes.
- Local CSV files live outside source code under `data/ohlcv/` and `data/fred/` for the first slices.
- `data/` remains gitignored because CSV files are runtime inputs, not source code.
- Unit and integration tests use committed fixture CSV files under `tests/fixtures/csv_import/`, not the local `data/` files.
- Runtime parameters use `input_uri`, with local path and `file://` support only.
- CSV dataset contracts are implemented in YAML so parsing parameters and dataset-specific metadata stay outside extractor code.
- YAML contracts define `source`, `entity`, input path/pattern, delimiter, encoding, required headers, column types, identity strategy, source record identity fields, observed timestamp/date column, and dbt selector.
- Phase 05 does not add a `config.yaml` setting for the contracts path.
- The generic CSV importer supports only `filename_pattern` and `value_column_header` identity strategies in Phase 05.
- CSV ingestion validates dataset-specific headers before load.
- Header validation is strict and pre-load. A mismatch fails the import before raw rows are written.
- Row-level value issues do not reject the whole file by default. They are stored as raw evidence with validation metadata when detected.
- CSV imports that insert only invalid raw rows do not trigger downstream dbt transforms.
- FRED series staging uses long form: `observation_date`, `series_id`, and `value`.
- OHLCV staging keeps source-specific timestamps and a canonical `observed_at` from the CSV `timestamp` column.
- OHLCV staging includes `asset_slug`, `source_asset_id`, `time_open`, `time_close`, `time_high`, `time_low`, `observed_at`, `open`, `high`, `low`, `close`, `volume`, `market_cap`, and `circulating_supply`.
- CSV rows are loaded into raw tables for the CSV import source/entities and then staged into typed dataset-specific columns.
- Extraction parses only the metadata needed for raw identity and observed timestamp/date. Typed business columns are cast in dbt staging.
- Raw payloads preserve original CSV columns and include `_felts` metadata such as contract name, input URI, row number, and parsed identity fields.
- Phase 05 stops at raw and staging for CSV contracts.
- The first OHLCV import derives asset identity from the filename rather than hard-coding it in the extractor.
- The first FRED series import derives series identity from the value column header and/or filename rather than hard-coding it in the extractor.
- CSV import flow accepts a contract name and an input URI, for example `contract=ohlcv` or `contract=fred_series`.
- Contract IDs come from the YAML `contracts` keys. For Phase 05, `ohlcv` and `fred_series` are both contract IDs and entity names.
- CSV import flow does not scan default directories when `input_uri` is omitted; `input_uri` is required in Phase 05.
- CSV import flow does not accept globs or multiple files in one run.
- CSV import rejects unsupported URI schemes such as `s3://`, `gs://`, `http://`, and `https://`.
- Prefect deployments exist for `ohlcv` and `fred_series`, but neither has a schedule.
- CLI and Prefect flows use the same CSV import runner.
- CLI shape supports both existing and new source commands:
  - `uv run felts coingecko run --entities global`
  - `uv run felts csv import --contract ohlcv --input-uri data/ohlcv/crypto-ohlcv-bitcoin-20260528.csv`
  - `uv run felts csv import --contract fred_series --input-uri data/fred/us_cpi-202605.csv`
- Re-importing the same file should insert zero new rows when row identities already exist, not fail the run and not duplicate rows.
- Implementation validation includes local CSV CLI runs for both sample files, raw table checks, staging model checks, and rerun idempotency checks.
- Prefect validation registers CSV deployments, triggers both unscheduled CSV deployments with `input_uri`, and confirms downstream `dbt-transform` runs through raw completion events.
- CSV raw completion events use `felts.raw.csv_import.ohlcv.completed` and `felts.raw.csv_import.fred_series.completed`.
- CSV CLI, Prefect flows, and tests report extracted, inserted, skipped duplicate, invalid, and failed counts using the same summary shape as existing sources.
- Cross-source joins remain possible in the intermediate layer after CSV staging models exist.

## Implementation Sequence

1. Refactor the CLI entrypoint into `src/felts/cli.py` while keeping the existing CoinGecko command working.
2. Add the CSV contracts YAML loader and validation for `src/felts/sources/csv_import/contracts.yaml`.
3. Add the generic standard-library CSV extractor for local paths and `file://` URIs.
4. Add the CSV import runner and CLI command using the same summary shape as existing sources.
5. Add raw and staging dbt models for `csv_import.raw_ohlcv` and `csv_import.raw_fred_series`.
6. Add CSV Prefect flow, events, deployments, and automations using unscheduled deployments.
7. Run local CLI smoke tests, raw table checks, staging model checks, rerun idempotency checks, and Prefect live tests.

## Out of Scope

- Web UI for CSV import.
- CoinMarketCap REST source.
- DeFi Llama GraphQL source.
- SFTP or object-store upload automation unless selected during grilling.
- `s3://`, `gs://`, or other object-store URI support.
- UI-driven CSV dataset registration.
- Column-value identity extraction unless a future CSV dataset requires it.
- File-level import blocking or processed-file state tracking.
- Automatic directory scanning when `input_uri` is omitted.
- Multi-file CSV import in a single flow or CLI run.
- Compressed CSV formats such as `.csv.gz` or `.zip`.
- WebSocket and Kafka streaming.
- Multi-target warehouse writes.
- CSV mart models.

## Grill Questions

- What exact raw entity names should the first CSV contracts use?
- Should source additions require a complete mart contribution, or is raw/staging enough?
- Should CSV imports append every file run, or should file-level identity prevent re-importing the same file?
- How strict should CSV schema/header validation be before raw load?
- How should each CSV dataset declare whether metadata such as asset identity comes from filename, columns, or flow parameters?
- Which identity extraction strategies are required for Phase 05?

## Draft CSV Contract Shape

```yaml
version: 1

contracts:
  ohlcv:
    source: csv_import
    entity: ohlcv
    input:
      default_path: data/ohlcv
      path_pattern: "crypto-ohlcv-{asset_slug}-{as_of_date}.csv"
      encoding: utf-8-sig
      delimiter: ";"
      has_header: true
    identity:
      strategy: filename_pattern
      fields:
        asset_slug: "{asset_slug}"
        as_of_date: "{as_of_date}"
    schema:
      required_headers:
        - timeOpen
        - timeClose
        - timeHigh
        - timeLow
        - name
        - open
        - high
        - low
        - close
        - volume
        - marketCap
        - circulatingSupply
        - timestamp
      column_types:
        timeOpen: timestamp
        timeClose: timestamp
        timeHigh: timestamp
        timeLow: timestamp
        name: string
        open: decimal
        high: decimal
        low: decimal
        close: decimal
        volume: decimal
        marketCap: decimal
        circulatingSupply: decimal
        timestamp: timestamp
    raw_record:
      source_record_id:
        fields:
          - asset_slug
          - timestamp
      observed_at_column: timestamp
    dbt:
      selector: stg_csv_import__ohlcv+

  fred_series:
    source: csv_import
    entity: fred_series
    input:
      default_path: data/fred
      path_pattern: "{dataset_slug}-{as_of_month}.csv"
      encoding: utf-8
      delimiter: ","
      has_header: true
    identity:
      strategy: value_column_header
      date_column: observation_date
      value_column_position: 2
      filename_fields:
        dataset_slug: "{dataset_slug}"
        as_of_month: "{as_of_month}"
    schema:
      required_headers:
        - observation_date
      allow_extra_headers: true
      value_columns:
        min: 1
        max: 1
      column_types:
        observation_date: date
        "*": decimal
    raw_record:
      source_record_id:
        fields:
          - series_id
          - observation_date
      observed_at_column: observation_date
    dbt:
      selector: stg_csv_import__fred_series+
```

# Phase 02 - First Source Vertical Slice

## Goal

Build one complete EL path from a real financial API into raw storage. CoinGecko is the first slice because it exercises REST extraction, authentication, pagination, validation, loading, and raw preservation against a real market-data source.

## Core Functionality

- REST extractor foundation.
- Synchronous HTTP client support using `httpx`.
- Minimal CLI command for local CoinGecko runs.
- Make targets for local CoinGecko run and opt-in smoke testing.
- Short user-facing documentation for running the CoinGecko slice locally.
- Reusable source run summary contracts.
- CoinGecko source package.
- Pydantic schemas for the first CoinGecko entities.
- Source-specific run entrypoint that composes extractor, schema registry, writer, and loader.
- A thin Prefect-compatible source flow function, without full deployment automation yet.

## Scope

- Create `src/felts/core/extractors/rest.py`.
- Create reusable source run summary contracts, for example under `src/felts/core/sources/`.
- Create `src/felts/sources/coingecko/`.
- Create CoinGecko validation schemas in `src/felts/sources/coingecko/schemas.py`.
- Create one `CoinGeckoExtractor` for Phase 02 with methods per supported entity.
- Implement the first CoinGecko entities in this order:
  - `coins_list`: `GET /coins/list`
  - `asset_platforms_list`: `GET /asset_platforms`
  - `global`: `GET /global`
  - `global_defi`: `GET /global/decentralized_finance_defi`
  - `coins_markets`: `GET /coins/markets`
- Implement validation through the shared writer.
- Load batches into the generic `raw.raw_records` table with `source="coingecko"` and entity-specific `entity` values.
- Add unit tests for extractor pagination, schema validation, source entrypoint composition, and failure behavior.
- Use `pytest-httpx` for mocked `httpx` HTTP responses in source tests.
- Add one narrow integration test that runs mocked CoinGecko HTTP responses through `RawWriter` and `PostgresRawLoader` into dockerized Postgres.

## Acceptance Criteria

- Running the CoinGecko source flow locally loads valid raw records into Postgres.
- Raw data is preserved as original API JSON.
- Invalid records are captured with validation errors according to the Phase 01 decision.
- Adding a second CoinGecko entity does not require changes to core modules.
- Source tests run without making live network calls.

## Decisions

- CoinGecko records use the Phase 01 generic raw landing table, `raw.raw_records`; Phase 02 does not create source-specific raw tables.
- Source-specific relational tables are deferred to dbt staging models, such as `stg_coingecko__coins_markets`, in Phase 03.
- Phase 02 remains EL-only and does not add dbt staging models.
- Tests may query `raw.raw_records` directly only to verify that extracted records landed.
- Reference-like CoinGecko entities such as `coins_list` and `asset_platforms_list` still load during each selected Phase 02 run.
- Phase 02 does not add freshness checks or skip-if-recently-loaded logic.
- CoinGecko source code lives under `src/felts/sources/coingecko/`.
- The shared REST extractor foundation lives at `src/felts/core/extractors/rest.py`.
- Phase 02 implements CoinGecko entities in this order: `coins_list`, `asset_platforms_list`, `global`, `global_defi`, then `coins_markets`.
- `coins_markets` is the first paginated CoinGecko entity in Phase 02; the earlier entities prove single-response list and object response handling first.
- CoinGecko validation schemas require the stable fields Felts depends on, but allow unknown provider fields so CoinGecko response additions do not break extraction.
- Phase 02 registers minimal tolerant validation schemas for all five CoinGecko entities.
- Raw payloads remain provider-shaped and are preserved in `RawRecord.payload`; validation models do not define the complete analytical contract.
- JSON-loadable but schema-invalid CoinGecko records do not block the source run; they are written as invalid raw records and included in source-level summary counts.
- Hard source-run failures are reserved for HTTP failures after retries, non-JSON responses, malformed top-level response shapes, database errors, and setup/programmer errors.
- CoinGecko extraction reads `COINGECKO_API_KEY` from project settings and `.env` for local live runs.
- Unit tests and source behavior tests use mocked HTTP responses and must not require a live `COINGECKO_API_KEY`.
- Integration tests may use dockerized Postgres but still use mocked CoinGecko HTTP responses.
- Phase 02 may include live CoinGecko smoke tests, but they are opt-in only, for example behind `FELTS_RUN_LIVE_TESTS=1` or a pytest marker.
- Normal `make test` and `make check` runs stay deterministic and do not call the live CoinGecko API.
- Live smoke tests, when explicitly invoked, exercise the full local EL path and may write to dockerized Postgres using capped Phase 02 settings.
- CoinGecko `source_record_id` mapping:
  - `coins_list`: CoinGecko coin `id`
  - `asset_platforms_list`: asset platform `id`
  - `global`: fixed value `global`
  - `global_defi`: fixed value `global_defi`
  - `coins_markets`: CoinGecko coin `id`
- CoinGecko `observed_at` mapping:
  - `coins_markets`: provider `last_updated` when present
  - `coins_list`, `asset_platforms_list`, `global`, and `global_defi`: `None` unless the provider response includes an explicit source observation timestamp
- `observed_at` represents provider observation time; `extracted_at` represents Felts ingestion time.
- `coins_markets` starts with `vs_currency="usd"` only, configurable through settings with default `usd`.
- Future multi-currency support must revisit `coins_markets` identity, likely using a composite `source_record_id` such as `{coin_id}:{vs_currency}`.
- `coins_markets` pagination is capped by default for Phase 02 local runs, for example `COINGECKO_MARKETS_PER_PAGE=250` and `COINGECKO_MARKETS_MAX_PAGES=1`.
- The cap proves pagination behavior without making every local run fetch the full market universe.
- Phase 02 adds CoinGecko settings:
  - `COINGECKO_API_KEY`
  - `COINGECKO_BASE_URL`, default `https://api.coingecko.com/api/v3`
  - `COINGECKO_REQUEST_TIMEOUT_SECONDS`, default `30`
  - `COINGECKO_RETRY_MAX_ATTEMPTS`, default `3`
  - `COINGECKO_MARKETS_VS_CURRENCY`, default `usd`
  - `COINGECKO_MARKETS_PER_PAGE`, default `250`
  - `COINGECKO_MARKETS_MAX_PAGES`, default `1`
- `.env.example` includes CoinGecko settings with safe placeholder/default values; the real `.env` remains uncommitted.
- Phase 02 sends `COINGECKO_API_KEY` using CoinGecko's demo API header, `x-cg-demo-api-key`; Pro API support is deferred.
- CoinGecko numeric settings validate sensible bounds at startup, such as positive timeout, retry count, page size, and max page count.
- `COINGECKO_API_KEY` is optional at settings construction so mocked tests and offline workflows do not require secrets.
- CoinGecko response-to-record mapping:
  - list endpoints emit one `ExtractedRecord` per list item
  - `global` emits one `ExtractedRecord` containing the response `data` object
  - `global_defi` emits one `ExtractedRecord` containing the response `data` object
  - `coins_markets` emits one `ExtractedRecord` per market row
- Phase 02 does not store request metadata such as endpoint path, query params, page number, or HTTP response time in `RawRecord.payload`.
- Operational request metadata is deferred to a later run/event logging design if needed.
- REST retry behavior is implemented in the shared REST extractor foundation.
- Phase 02 uses synchronous `httpx` for REST extraction.
- The shared REST extractor foundation owns low-level request, retry, timeout, and JSON parsing behavior only.
- `coins_markets` pagination remains CoinGecko-specific in Phase 02; no generic pagination abstraction is introduced yet.
- Phase 02 retries transient HTTP statuses only: `429`, `500`, `502`, `503`, and `504`.
- REST retries use exponential backoff with a small max attempt count, default `3`, and respect `Retry-After` when the provider sends it.
- After retries are exhausted, the current entity fails clearly; Phase 02 does not silently skip failed pages.
- Phase 02 uses the core exception hierarchy for extraction failures, adding a generic extraction exception only if needed.
- Phase 02 does not introduce CoinGecko-specific exception classes.
- CoinGecko exposes a plain Python entrypoint, such as `run_coingecko_source(...)`, that composes settings, extractor, schema registry, writer, and loader.
- Any Prefect flow in Phase 02 is a thin wrapper around the plain Python entrypoint rather than the owner of source logic.
- Phase 02 includes a minimal CLI command, for example `felts coingecko run --entities coins_list global`, that calls the plain Python entrypoint and prints write counts.
- The CoinGecko CLI defaults to all Phase 02 entities in the agreed order and accepts `--entities` to run a subset.
- CoinGecko runs fail fast by default when a selected entity fails; Phase 02 does not add `--continue-on-error`.
- Phase 02 adds explicit Make targets for local CoinGecko usage, such as `make coingecko-run` and `make coingecko-smoke`.
- `make check` remains offline and does not call CoinGecko.
- Phase 02 adds short run instructions, such as `.env` setup, starting Postgres, `make coingecko-run`, and optional smoke testing.
- The CoinGecko source entrypoint returns a source-level summary grouped by entity, including counts such as `extracted`, `inserted`, `skipped_duplicate`, and `invalid`.
- CLI and Prefect wrappers report source-level outcomes rather than exposing loader internals directly.
- Source-level summaries are reusable core contracts, for example `EntityRunSummary` and `SourceRunSummary`, rather than CoinGecko-only structures.
- CoinGecko validation schemas live in one `schemas.py` module for Phase 02; split by entity later only if the schemas become large.
- Phase 02 uses one `CoinGeckoExtractor` class with methods per supported entity, rather than one extractor class per entity.
- CoinGecko extractor method names match entity names, for example `extract_coins_list()` and `extract_global_defi()`.
- The CoinGecko package defines one central ordered entity list used by the CLI, source entrypoint, tests, and summaries.
- CoinGecko endpoint metadata lives in Python constants or typed structures, not YAML, covering details such as entity name, endpoint path, response shape, and source-record ID field.

## Out of Scope

- CoinMarketCap, DeFi Llama, CSV import, WebSocket, or Kafka sources.
- Full Prefect deployment registration.
- dbt mart models.
- Backfill framework.

CSV import remains an early Felts source goal, but it is intentionally deferred from Phase 02 because local file sources need separate decisions for file identity, schema/header handling, parsing, duplicate rows, and archival.

## Resolved Grill Questions

- Implement CoinGecko entities in this order: `coins_list`, `asset_platforms_list`, `global`, `global_defi`, then `coins_markets`.
- Keep normal tests mocked and offline; live CoinGecko smoke tests are opt-in only.
- Retry transient HTTP failures with bounded exponential backoff and `Retry-After` support.
- Use minimal tolerant validation schemas that allow unknown provider fields.

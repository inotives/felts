# Phase 02 - First Source Vertical Slice

## Goal

Build one complete EL path from a real financial API into raw storage. CoinGecko is the recommended first slice because it exercises REST extraction, pagination, validation, loading, and raw preservation without API-key complexity for the basic endpoints.

## Core Functionality

- REST extractor foundation.
- CoinGecko source package.
- Pydantic schemas for the first CoinGecko entities.
- Source-specific loader wrapper.
- A thin Prefect-compatible source flow function, without full deployment automation yet.

## Scope

- Create `pipeline/core/extractors/rest_extractor.py`.
- Create `pipeline/sources/coingecko/`.
- Implement `coins_markets`, `coins_list`, and `global` entity extraction.
- Implement validation through the shared writer.
- Load batches into `raw.coingecko__{entity}` tables.
- Add unit tests for extractor pagination, schema validation, and loader invocation.

## Acceptance Criteria

- Running the CoinGecko source flow locally loads valid raw records into Postgres.
- Raw data is preserved as original API JSON.
- Invalid records are captured with validation errors according to the Phase 01 decision.
- Adding a second CoinGecko entity does not require changes to core modules.
- Source tests run without making live network calls.

## Out of Scope

- CoinMarketCap, DeFi Llama, CSV import, WebSocket, or Kafka sources.
- Full Prefect deployment registration.
- dbt mart models.
- Backfill framework.

## Grill Questions

- Which CoinGecko entity should be the first production-quality entity: `coins_markets`, `coins_list`, or `global`?
- Should this phase use live API smoke tests in addition to mocked unit tests?
- What rate-limit behavior is acceptable for MVP retries?
- Should source schemas be strict, or should unknown fields be allowed to preserve provider changes?

---
id: task-0029
title: "Phase 16: CCXT dbt models"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-28
priority: normal
parent: ""
depends_on:
  - task-0028
---







# Task

## Context

Task 0028 lands raw CCXT ticker and order book records for Binance `BTC/USDT`.
This task turns those raw records into provider-native staging and mart models.

Source of truth:

- `docs/phases/phase_16_ccxt_exchange_market_snapshots.md`

## Goal

Add CCXT staging and mart models for ticker snapshots and top-20 order book
snapshots.

## Scope

- Add staging models in the `ccxt` schema:
  - `stg_ccxt__tickers`
  - `stg_ccxt__order_books`
- Add mart models in the `ccxt` schema:
  - `mart_ccxt__tickers`
  - `mart_ccxt__order_book_snapshots`
- Keep both staging models at grain:

  ```text
  exchange_id, symbol, observed_at
  ```

- Keep ticker mart at one row per ticker snapshot.
- Keep order book mart at one row per order book snapshot.
- Preserve top-20 `bids` and `asks` arrays as JSON in the order book mart.
- Add order book mart `spread` and `mid_price` from best bid/ask.
- Add dbt docs and tests for required fields and uniqueness.

## Planner Notes

Do not add a flattened order book levels mart in Phase 16.

Do not add intermediate CCXT models unless strictly needed for the two requested
marts.

## Implementation Plan

1. Add CCXT staging SQL and YAML docs/tests.
2. Add CCXT mart SQL and YAML docs/tests.
3. Ensure dbt config materializes models in the `ccxt` schema consistently with
   source-owned provider schemas.
4. Run dbt parse and focused dbt run/test selectors when local dbt dependencies
   and Postgres are available.
5. Record exact dbt command outcomes or environment blockers in `## Notes`.

## Acceptance Criteria

- [x] `stg_ccxt__tickers` builds from raw CCXT ticker records.
- [x] `stg_ccxt__order_books` builds from raw CCXT order book records.
- [x] `mart_ccxt__tickers` builds from ticker staging.
- [x] `mart_ccxt__order_book_snapshots` builds from order book staging.
- [x] Ticker staging and mart grain is `exchange_id, symbol, observed_at`.
- [x] Order book staging and mart grain is `exchange_id, symbol, observed_at`.
- [x] Order book mart preserves top-20 bid and ask arrays as JSON.
- [x] Order book mart exposes best bid, best ask, spread, and mid price.
- [x] Focused dbt verification or blocker details are recorded in `## Notes`.

## Notes

- Added the CCXT raw source declaration at `transforms/models/sources/ccxt.yml`.
- Added staging models:
  - `transforms/models/staging/ccxt/stg_ccxt__tickers.sql`
  - `transforms/models/staging/ccxt/stg_ccxt__order_books.sql`
- Added mart models:
  - `transforms/models/marts/ccxt/mart_ccxt__tickers.sql`
  - `transforms/models/marts/ccxt/mart_ccxt__order_book_snapshots.sql`
- Added CCXT dbt docs/tests in
  `transforms/models/staging/ccxt/_ccxt__models.yml`.
- Updated `transforms/dbt_project.yml` so CCXT staging and marts materialize in
  the `ccxt` schema.
- Focused verification:
  - `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms`
    -> success
  - `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms --select ccxt_market_universe`
    -> `PASS=1`
  - `./.venv/bin/felts ccxt run --entities ticker order_book`
    -> `ticker extracted=1 inserted=1`, `order_book extracted=1 inserted=1`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
    -> `PASS=4`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
    -> `PASS=24`
- Verification note:
  - the first sandboxed `dbt seed/run/test` attempts failed with local Postgres
    access denied at `localhost:5432`.
  - the first escalated `dbt run/test` attempts raced the live ingest because I
    launched them in parallel, so they failed before the raw CCXT tables
    existed.
  - rerunning `dbt run` and `dbt test` sequentially after the live ingest
    completed succeeded.
- Reviewer verification on 2026-07-28:
  - Re-ran `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms`
    -> success
  - Sandboxed live smoke failed with both entities marked failed, but the same
    command succeeded unsandboxed, confirming the sandbox/network limitation
    rather than a Task 29 model defect:
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/felts ccxt run --entities ticker order_book`
      -> `entity=ticker extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`
      -> `entity=order_book extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`
  - Re-ran focused dbt commands unsandboxed against local Postgres:
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms --select ccxt_market_universe`
      -> `PASS=1`
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
      -> `PASS=4`
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
      -> `PASS=24`
  - Direct Postgres spot-check on July 28, 2026:
    - `ccxt.mart_ccxt__tickers` rows: `2`
    - `ccxt.mart_ccxt__order_book_snapshots` rows: `2`
    - latest mart order-book snapshot for `binance` `BTC/USDT` had
      `best_bid=63453.26`, `best_ask=63453.27`, `spread=0.01`,
      `mid_price=63453.265`, `jsonb_array_length(bids)=20`,
      `jsonb_array_length(asks)=20`
  - No review findings. The staging/mart grain, preserved top-20 arrays, and
    derived spread/mid-price fields all match the Phase 16 contract.

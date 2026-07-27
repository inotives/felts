---
id: task-0029
title: "Phase 16: CCXT dbt models"
type: task
status: pending
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
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

- [ ] `stg_ccxt__tickers` builds from raw CCXT ticker records.
- [ ] `stg_ccxt__order_books` builds from raw CCXT order book records.
- [ ] `mart_ccxt__tickers` builds from ticker staging.
- [ ] `mart_ccxt__order_book_snapshots` builds from order book staging.
- [ ] Ticker staging and mart grain is `exchange_id, symbol, observed_at`.
- [ ] Order book staging and mart grain is `exchange_id, symbol, observed_at`.
- [ ] Order book mart preserves top-20 bid and ask arrays as JSON.
- [ ] Order book mart exposes best bid, best ask, spread, and mid price.
- [ ] Focused dbt verification or blocker details are recorded in `## Notes`.

## Notes

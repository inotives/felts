---
id: task-0025
title: "Phase 15: CoinGecko daily OHLC rollup dbt"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on:
  - task-0024
---




# Task

## Context

Task 0024 changes raw OHLC capture to provider 4-hour candles. This task derives
daily OHLC in dbt and rewires the public OHLC/OHLCV marts to use that rollup.

Source of truth:

- `docs/phases/phase_15_coingecko_public_ohlc_rollup_fix.md`

## Goal

Add a CoinGecko intermediate daily OHLC rollup model and use it for the existing
OHLC and OHLCV marts.

## Scope

- Keep `stg_coingecko__coins_ohlc` provider-shaped at 4-hour candle grain.
- Add intermediate model `int_coingecko__coin_ohlc_daily_rollups`.
- Configure the intermediate model path/schema consistently with CoinGecko
  models.
- Intermediate grain:
  - `coin_id`
  - `vs_currency`
  - `observed_at`
- Derive intermediate `observed_at` from UTC close-date of staging `observed_at`.
- Roll up daily OHLC:
  - `open` = first 4-hour candle open for the UTC close-date
  - `high` = max high for the UTC close-date
  - `low` = min low for the UTC close-date
  - `close` = last 4-hour candle close for the UTC close-date
- Filter rollup source rows to `days = 30` and `interval = '4h'`.
- Change `mart_coingecko__coin_ohlc_candles` to read from the intermediate model.
- Change `mart_coingecko__coin_ohlcv_daily` to join the intermediate model to
  `stg_coingecko__coins_market_chart`.
- Add dbt docs/tests for intermediate, OHLC mart, and OHLCV mart daily grain.

## Planner Notes

The existing `mart_coingecko__coin_ohlc_candles` intentionally changes to daily
rollup grain in Phase 15.

Do not expose the intermediate model through MCP.

## Implementation Plan

1. Add `transforms/models/intermediate/coingecko/` and dbt project config if
   needed.
2. Add SQL for `int_coingecko__coin_ohlc_daily_rollups`.
3. Rewire OHLC and OHLCV mart SQL to use the intermediate rollup.
4. Update dbt YAML docs/tests for staging, intermediate, and mart grain.
5. Run focused dbt parse/run/test selectors when local dbt dependencies are
   available.

## Acceptance Criteria

- [ ] `stg_coingecko__coins_ohlc` remains provider candle grain.
- [ ] `int_coingecko__coin_ohlc_daily_rollups` builds daily OHLC from corrected
      4-hour rows only.
- [ ] Intermediate uniqueness is `coin_id, vs_currency, observed_at`.
- [ ] `mart_coingecko__coin_ohlc_candles` reads from the intermediate model.
- [ ] `mart_coingecko__coin_ohlcv_daily` joins the intermediate model to daily
      market-chart metrics.
- [ ] OHLCV volume still comes from `coins_market_chart`.
- [ ] Focused dbt verification or blocker details are recorded in `## Notes`.

## Notes

- Added `transforms/models/intermediate/coingecko/int_coingecko__coin_ohlc_daily_rollups.sql`
  and `transforms/dbt_project.yml` intermediate-path config so Phase 15 daily
  OHLC rollups build in the `coingecko` schema.
- The intermediate rollup filters `stg_coingecko__coins_ohlc` to corrected
  `days = 30` and `interval = '4h'` rows, derives UTC daily `observed_at`,
  uses the first 4-hour candle open, max high, min low, and last 4-hour candle
  close, and keeps one row per `coin_id, vs_currency, observed_at`.
- Rewired `mart_coingecko__coin_ohlc_candles` and
  `mart_coingecko__coin_ohlcv_daily` to read from the intermediate daily OHLC
  rollup instead of raw staging OHLC rows.
- Updated CoinGecko dbt model docs/tests so the intermediate model, OHLC mart,
  and OHLCV mart assert daily UTC grain, and the OHLC rollup surface asserts
  `days = 30` and `interval = 'daily'`.
- Verification:
  - `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms`
  - `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - Results:
    - `dbt parse` completed successfully
    - `dbt seed`: `PASS=3`
    - `dbt run`: `PASS=6`
    - `dbt test`: `PASS=61`
- Reviewer verification on Monday, July 27, 2026:
  - `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms`
  - sandboxed `dbt seed` hit localhost Postgres permission denial, then reran
    unsandboxed:
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - Results:
    - `dbt seed`: `PASS=3`
    - `dbt run`: `PASS=6`
    - `dbt test`: `PASS=61`
  - Warehouse spot-check:
    - corrected staging OHLC rows: `540`
    - intermediate daily OHLC rows: `93`
    - `mart_coingecko__coin_ohlc_candles` rows: `93`
    - `mart_coingecko__coin_ohlcv_daily` rows: `90`
  - Sample July 27, 2026 BTC rollup matched staging math exactly:
    - daily `open` = first 4h open
    - daily `high` = max 4h high
    - daily `low` = min 4h low
    - daily `close` = last 4h close
  - The 3-row gap between OHLC and OHLCV is the expected current-day join gap:
    July 27, 2026 OHLC rows existed for BTC, ETH, and SOL before same-day
    `coins_market_chart` metrics were available, so they do not yet appear in
    `mart_coingecko__coin_ohlcv_daily`.

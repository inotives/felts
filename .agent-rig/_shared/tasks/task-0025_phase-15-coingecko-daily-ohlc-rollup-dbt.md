---
id: task-0025
title: "Phase 15: CoinGecko daily OHLC rollup dbt"
type: task
status: blocked
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

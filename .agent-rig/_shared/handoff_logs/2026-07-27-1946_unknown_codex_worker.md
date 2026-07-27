---
agent: worker
role: worker
tool: codex
task: task-0025
task_title: "Phase 15: CoinGecko daily OHLC rollup dbt"
status: handoff
---

# Summary

Implemented the Phase 15 CoinGecko daily OHLC rollup dbt work.

# Changes

- Added `transforms/models/intermediate/coingecko/int_coingecko__coin_ohlc_daily_rollups.sql`
  to roll corrected `days = 30`, `interval = '4h'` staging candles into one
  UTC daily OHLC row per `coin_id, vs_currency, observed_at`.
- Added `intermediate/coingecko` model-path config in `transforms/dbt_project.yml`.
- Rewired:
  - `transforms/models/marts/coingecko/mart_coingecko__coin_ohlc_candles.sql`
  - `transforms/models/marts/coingecko/mart_coingecko__coin_ohlcv_daily.sql`
  so both now read from the intermediate daily rollup.
- Updated `transforms/models/staging/coingecko/_coingecko__models.yml` docs/tests
  for the new intermediate model and the daily-grain OHLC/OHLCV marts.

# Verification

- `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms`
  - completed successfully
- `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
  - `PASS=3`
- `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `PASS=6`
- `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `PASS=61`

# Notes

- The rollup model keeps staging provider grain untouched and filters to Phase 15
  corrected OHLC rows only, so older Phase 14 `days=90` or `interval=daily`
  rows do not affect daily output.

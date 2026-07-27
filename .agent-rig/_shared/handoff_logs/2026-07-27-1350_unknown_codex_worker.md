---
agent: worker
role: worker
tool: codex
task: task-0021
task_title: "Phase 14: CoinGecko market metrics and OHLCV dbt models"
status: handoff
---

# Summary

Implemented the Phase 14 CoinGecko dbt models for `task-0021` and moved the
task to `review`.

# Changes

- Added `raw_coins_market_chart` to `transforms/models/sources/coingecko.yml`.
- Added staging model:
  `transforms/models/staging/coingecko/stg_coingecko__coins_market_chart.sql`
  with grain `coin_id, vs_currency, interval, observed_at`.
- Added marts:
  - `transforms/models/marts/coingecko/mart_coingecko__coin_daily_market_metrics.sql`
  - `transforms/models/marts/coingecko/mart_coingecko__coin_ohlcv_daily.sql`
- Updated existing OHLC models to expose `interval`:
  - `transforms/models/staging/coingecko/stg_coingecko__coins_ohlc.sql`
  - `transforms/models/marts/coingecko/mart_coingecko__coin_ohlc_candles.sql`
- Added dbt docs/tests in
  `transforms/models/staging/coingecko/_coingecko__models.yml` for the new
  staging/mart models plus the new OHLC `interval` field.
- Backward-compatibility fix: legacy pre-Phase-14 OHLC raw rows without
  `payload.interval` now surface `provider_default` in staging instead of
  failing new not-null tests.

# Verification

- `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms`
  - passed
- `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
  - `PASS=3 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=3`
- `./.venv/bin/felts coingecko run --entities coins_market_chart`
  - `source=coingecko entity=coins_market_chart extracted=270 inserted=270 skipped_duplicate=0 invalid=0 failed=0`
- `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `PASS=5 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=5`
- `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `PASS=45 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=45`

# Notes

- On Monday, July 27, 2026, a live local run of
  `./.venv/bin/felts coingecko run --entities coins_ohlc coins_market_chart`
  failed on `coins_ohlc` because CoinGecko returned `400 Bad Request` for
  `/coins/{id}/ohlc?...&interval=daily`.
- Task 21 itself is implemented and verified at the dbt layer using fresh live
  `coins_market_chart` raw data plus the existing local OHLC raw table, but the
  upstream live OHLC interval issue remains relevant for review of task 20 /
  Phase 14 end-to-end ingest behavior.

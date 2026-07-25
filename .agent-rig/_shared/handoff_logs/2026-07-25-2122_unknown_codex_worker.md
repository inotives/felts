---
agent: worker
role: worker
tool: codex
task: task-0013
task_title: "Phase 12: mart-first MCP allowlist"
status: handoff
---

# Summary

Updated `settings/felts-prod-data-views.txt` from the mixed staging/mart set to the
Phase 12 mart-first allowlist:

- `alphavantage.mart_alphavantage__daily_prices`
- `coingecko.mart_coingecko__asset_platforms`
- `coingecko.mart_coingecko__coin_market_snapshots`
- `coingecko.mart_coingecko__coins`
- `coingecko.mart_coingecko__global_defi_snapshots`
- `coingecko.mart_coingecko__global_market_snapshots`
- `csv_import.mart_csv_import__fred_observations`
- `csv_import.mart_csv_import__ohlcv`
- `felts.mart_felts__asset_platforms`
- `felts.mart_felts__asset_provider_mappings`
- `felts.mart_felts__assets`

Removed replaced staging entries for Alpha Vantage, CoinGecko, and CSV import.

# Verification

- Sanity-checked the final allowlist file contents locally.
- No focused tests were run in this task; task `0014` owns the unit test and docs
  update for this contract.

# Notes

- No SQL safety behavior was changed.

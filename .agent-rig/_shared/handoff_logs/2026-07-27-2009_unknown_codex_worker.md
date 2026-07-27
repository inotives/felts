---
agent: worker
role: worker
tool: codex
task: task-0026
task_title: "Phase 15: MCP and docs alignment"
status: handoff
---

# Summary

Implemented the Phase 15 MCP and docs alignment work without changing the
committed MCP allowlist.

# Changes

- Left `settings/felts-prod-data-views.txt` unchanged.
- Updated `tests/unit/test_prod_data_mcp.py` to explicitly reject:
  - `coingecko.int_coingecko__coin_ohlc_daily_rollups`
  - `coingecko.raw_coins_ohlc`
  - `coingecko.stg_coingecko__coins_ohlc`
- Updated `docs/mcp/felts-prod-data.md` to describe:
  - `coingecko.mart_coingecko__coin_ohlc_candles` as daily UTC OHLC rollup
    output derived from 30-day public-compatible OHLC capture
  - `coingecko.mart_coingecko__coin_ohlcv_daily` as daily OHLC rollup joined to
    market-chart metrics
  - non-exposure of intermediate/raw/staging OHLC relations
- Updated `README.md` and `docs/project_specs.md` so the current branch docs say
  Phase 15 is implemented and describe the corrected public OHLC contract,
  provider 4-hour staging, intermediate daily rollups, and derived daily OHLCV.

# Verification

- `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
  - `40 passed in 0.32s`

# Notes

- No production reconciliation command was run.

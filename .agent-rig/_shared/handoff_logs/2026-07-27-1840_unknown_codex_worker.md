---
agent: worker
role: worker
tool: codex
task: task-0024
task_title: "Phase 15: CoinGecko public OHLC source fix"
status: handoff
---

# Summary

Implemented the Phase 15 public CoinGecko OHLC source fix.

# Changes

- Updated `src/felts/sources/coingecko/extractor.py` to:
  - default `coins_ohlc` to `days=30`
  - remove the OHLC request `interval` parameter
  - store OHLC raw payload `interval` as `4h`
  - keep `coins_market_chart` on a separate `market_chart_days=90` path so its
    `days=90&interval=daily` contract stays unchanged
- Updated focused OHLC assertions in:
  - `tests/unit/sources/coingecko/test_extractor.py`
  - `tests/unit/sources/coingecko/test_runner.py`

# Verification

- `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
- Result: `31 passed in 1.26s`

# Notes

- Deployment schedule coverage for `coins_ohlc` and event selector coverage for
  `stg_coingecko__coins_ohlc+` stayed green without code changes.

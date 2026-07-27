---
agent: worker
role: worker
tool: codex
task: task-0020
task_title: "Phase 14: CoinGecko market-chart source and schedules"
status: handoff
---

# Summary

Implemented the Phase 14 CoinGecko raw/source work for `task-0020` and moved
the task to `review`.

# Changes

- Added `coins_market_chart` to CoinGecko supported entities, endpoint
  definitions, dbt selector mapping, schema registry, runner support, and
  Prefect deployment specs.
- Added market-chart extraction for mapped CoinGecko assets using
  `/coins/{coin_id}/market_chart` with `vs_currency`, `days=90`, and
  `interval=daily`.
- Flattened market-chart responses by shared timestamp across `prices`,
  `market_caps`, and `total_volumes`, with raw identity
  `coin_id|vs_currency|interval|timestamp_ms`.
- Updated OHLC extraction to request `interval=daily` and to include
  `interval` in the raw payload while keeping OHLC raw identity
  `coin_id|vs_currency|timestamp_ms`.
- Updated focused unit tests for extractor shape validation, schema coverage,
  runner support, event selector wiring, and Phase 14 schedule changes.

# Verification

- `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
  - `31 passed in 2.84s`
- `./.venv/bin/ruff check src/felts/sources/coingecko tests/unit/sources/coingecko`
  - `All checks passed!`
- `./.venv/bin/ruff format --check src/felts/sources/coingecko tests/unit/sources/coingecko`
  - `15 files already formatted`

# Notes

- This task covers only the raw/source-side Phase 14 work. The dbt models,
  marts, and MCP allowlist/doc updates described in the phase doc remain for
  later tasks.

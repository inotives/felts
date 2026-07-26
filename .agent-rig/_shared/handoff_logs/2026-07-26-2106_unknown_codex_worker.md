---
agent: worker
role: worker
tool: codex
task: task-0016
task_title: "Phase 13: CoinGecko OHLC source capture"
status: handoff
---

# Summary

Implemented the Phase 13 CoinGecko source-side OHLC capture path.

What changed:

- added `coins_ohlc` as a supported CoinGecko entity
- added selector mapping `stg_coingecko__coins_ohlc+`
- added daily deployment schedule `0 3 * * *` UTC
- kept raw completion events wired to the same selector
- added raw validation schema for OHLC payloads
- added extractor support for `/coins/{coin_id}/ohlc` with `vs_currency` and
  `days=90`
- defaulted CoinGecko IDs from
  `transforms/seeds/felts/asset_provider_mappings.csv`, filtered to
  `provider_source=coingecko` and de-duplicated
- converted provider OHLC array rows into raw object payloads
- set duplicate-safe identity to `coin_id|vs_currency|timestamp_ms`
- derived `observed_at` from `timestamp_ms`

# Verification

- `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py -q` -> `11 passed in 0.14s`
- `./.venv/bin/pytest tests/unit/sources/coingecko/test_runner.py -q` -> `6 passed in 0.14s`
- `./.venv/bin/pytest tests/unit/sources/coingecko/test_deployments.py -q` -> `2 passed in 1.15s`
- `./.venv/bin/pytest tests/unit/sources/coingecko/test_events.py -q` -> `4 passed in 0.71s`
- `./.venv/bin/ruff check src/felts/sources/coingecko tests/unit/sources/coingecko` -> `All checks passed!`
- `./.venv/bin/ruff format --check src/felts/sources/coingecko tests/unit/sources/coingecko` -> `15 files already formatted`
- `./.venv/bin/python -m mypy src/felts/sources/coingecko` -> `Success: no issues found in 10 source files`

# Notes

- No dbt source, staging, mart, or MCP allowlist changes were made in this task.
- Task `0017` can now add `raw_coins_ohlc`, `stg_coingecko__coins_ohlc`, and
  `mart_coingecko__coin_ohlc_candles` on top of this extraction path.

---
agent: worker
role: worker
tool: codex
task: task-0022
task_title: "Phase 14: OHLCV MCP access and docs"
status: handoff
---

# Summary

Implemented the Phase 14 MCP allowlist/doc/test updates for `task-0022` and
moved the task to `review`.

# Changes

- Added the Phase 14 marts to
  `settings/felts-prod-data-views.txt`:
  - `coingecko.mart_coingecko__coin_daily_market_metrics`
  - `coingecko.mart_coingecko__coin_ohlcv_daily`
- Updated `tests/unit/test_prod_data_mcp.py` so focused MCP coverage now:
  - asserts both new marts are committed in the allowlist
  - accepts bounded selects from both new marts
  - rejects `coingecko.stg_coingecko__coins_market_chart`
  - covers `describe_allowed_view` for both new marts
- Updated `docs/mcp/felts-prod-data.md` so both Phase 14 marts appear in the
  preferred mart-first access surface.

# Verification

- `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
  - `37 passed in 0.23s`
- `./.venv/bin/ruff check tests/unit/test_prod_data_mcp.py`
  - `All checks passed!`
- `./.venv/bin/ruff format --check tests/unit/test_prod_data_mcp.py`
  - `1 file already formatted`

# Notes

- No production reconciliation command was run.
- This task is scoped to the committed allowlist plus MCP docs/tests only; no
  SQL safety-policy changes were needed.

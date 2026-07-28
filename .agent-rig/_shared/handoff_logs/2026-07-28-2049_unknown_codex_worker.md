---
agent: worker
role: worker
tool: codex
task: task-0030
task_title: "Phase 16: CCXT MCP and docs alignment"
status: handoff
---

# Summary

Implemented the Phase 16 CCXT MCP/docs alignment slice and moved `task-0030` to
review.

# What Changed

- Added the two CCXT marts to the committed MCP allowlist in
  `settings/felts-prod-data-views.txt`:
  - `ccxt.mart_ccxt__order_book_snapshots`
  - `ccxt.mart_ccxt__tickers`
- Updated `tests/unit/test_prod_data_mcp.py` to:
  - include the two CCXT marts in the committed allowlist assertion
  - allow schema-qualified selects from both CCXT marts
  - reject `ccxt.raw_ticker`, `ccxt.raw_order_book`,
    `ccxt.stg_ccxt__tickers`, and `ccxt.stg_ccxt__order_books`
  - resolve schema-qualified `describe_allowed_view(...)` lookups for both CCXT marts
  - load the CCXT dbt mart description through `load_dbt_descriptions()`
- Updated docs:
  - `docs/mcp/felts-prod-data.md`
  - `README.md`
  - `docs/project_specs.md`

# Verification

- `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
  - `48 passed in 0.35s`
- `./.venv/bin/ruff check tests/unit/test_prod_data_mcp.py`
  - `All checks passed!`
- `./.venv/bin/ruff format --check tests/unit/test_prod_data_mcp.py`
  - `1 file already formatted`

# Notes

- No production reconciliation command was run.
- `scripts/update-prod-data-access.sh` was intentionally not executed in this task.

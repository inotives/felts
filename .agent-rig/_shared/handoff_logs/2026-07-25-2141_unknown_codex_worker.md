---
agent: worker
role: worker
tool: codex
task: task-0013
task_title: "Phase 12: mart-first MCP allowlist"
status: handoff
---

# Summary

Reviewer return on July 25, 2026 said the allowlist change was correct but
`tests/unit/test_prod_data_mcp.py` still asserted the removed staging surface.

Updated `tests/unit/test_prod_data_mcp.py` to match the committed Phase 12
mart-first allowlist:

- added the new Alpha Vantage, CoinGecko, CSV import, and Felts mart names to
  `test_load_allowed_views_reads_committed_allowlist`
- changed the unbounded aggregate acceptance case from
  `public.stg_alphavantage__time_series_daily` to
  `alphavantage.mart_alphavantage__daily_prices`

# Verification

- `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q` -> `16 passed in 0.22s`
- `./.venv/bin/pytest tests/unit/test_deploy_script_guards.py -q` -> `7 passed in 0.01s`

# Notes

- Task `0013` now carries both the allowlist change and the minimal focused test
  fix needed to keep MCP coverage green after the policy update.

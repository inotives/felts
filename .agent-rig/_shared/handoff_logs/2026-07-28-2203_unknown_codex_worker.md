---
agent: worker
role: worker
tool: codex
task: task-0031
task_title: "Phase 16: verification and close-out"
status: handoff
---

# Summary

Completed the Phase 16 verification pass and moved `task-0031` to review.

# Verification

- Focused CCXT source tests
  - `./.venv/bin/pytest tests/unit/sources/ccxt/test_extractor.py tests/unit/sources/ccxt/test_runner.py tests/unit/sources/ccxt/test_cli.py tests/unit/test_top_level_cli.py -q`
  - `13 passed in 0.19s`
- Focused MCP tests
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
  - `48 passed in 0.39s`
- Fast local checks
  - `./.venv/bin/ruff check .`
  - `All checks passed!`
  - `./.venv/bin/ruff format --check .`
  - `116 files already formatted`
  - `./.venv/bin/python -m mypy`
  - `Success: no issues found in 104 source files`
  - `./.venv/bin/pytest tests/unit -q`
  - `157 passed in 1.56s`
- Focused dbt checks
  - `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
  - `PASS=4`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
  - `PASS=4`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
  - `PASS=24`
- Live CCXT Binance smoke
  - `./.venv/bin/felts ccxt run --entities ticker order_book`
  - `entity=ticker extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`
  - `entity=order_book extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`

# Evidence

- Direct Postgres inspection on July 28, 2026:
  - raw ticker rows: `3`
  - raw order-book rows: `3`
  - staging ticker rows: `3`
  - staging order-book rows: `3`
  - mart ticker rows: `2`
  - mart order-book rows: `2`
  - latest ticker mart row: `binance BTC/USDT last=63453.26 bid=63453.26 ask=63453.27`
  - latest order-book mart row:
    `binance BTC/USDT best_bid=63453.26 best_ask=63453.27 spread=0.01 mid_price=63453.265 bids=20 asks=20`
- MCP policy inspection:
  - `validate_query('select observed_at, last_price from ccxt.mart_ccxt__tickers limit 5')`
    normalizes successfully.
  - `validate_query('select observed_at, best_bid, best_ask from ccxt.mart_ccxt__order_book_snapshots limit 5')`
    normalizes successfully.

# Notes

- The first full `mypy` and `pytest tests/unit` runs failed due to duplicate
  `test_cli` / `test_runner` / `test_extractor` module names across source test
  folders. I fixed that by adding `__init__.py` package markers under
  `tests/unit/sources/`, `tests/unit/sources/ccxt/`,
  `tests/unit/sources/coingecko/`, and `tests/unit/sources/csv_import/`.
- Sandboxed dbt still cannot connect to local Postgres on `localhost:5432`, so
  final dbt commands were run outside the sandbox.
- No production reconciliation command was run. `scripts/update-prod-data-access.sh`
  was not executed.

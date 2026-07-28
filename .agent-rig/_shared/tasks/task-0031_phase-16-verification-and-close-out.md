---
id: task-0031
title: "Phase 16: verification and close-out"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-28
priority: normal
parent: ""
depends_on:
  - task-0030
---







# Task

## Context

Tasks 0028 through 0030 implement the Phase 16 CCXT public exchange market
snapshot slice.

Source of truth:

- `docs/phases/phase_16_ccxt_exchange_market_snapshots.md`

## Goal

Run final verification for Phase 16, including the required live CCXT Binance
`BTC/USDT` ticker and top-20 order book smoke.

## Scope

- Run fast checks:
  - `./.venv/bin/ruff check .`
  - `./.venv/bin/ruff format --check .`
  - `./.venv/bin/python -m mypy`
  - `./.venv/bin/pytest tests/unit`
- Run focused CCXT source tests.
- Run focused MCP tests.
- Run dbt checks:
  - `dbt seed`
  - `dbt run --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
  - `dbt test --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
- Run required live smoke:
  - `./.venv/bin/felts ccxt run --entities ticker order_book`
- Inspect raw, staging, mart, and MCP access evidence for Binance `BTC/USDT`.
- Record exact command evidence in `## Notes`.
- Do not run `scripts/update-prod-data-access.sh` against production.
- Do not archive the Phase 16 doc unless the human explicitly asks after merge.

## Planner Notes

The live smoke must target CCXT `binance`. If Binance public API access is
blocked from the execution environment, record the exact CCXT error and leave the
task blocked until the exchange target changes by follow-up decision.

If sandboxed dbt cannot connect to local Postgres on `localhost:5432`, rerun dbt
outside the sandbox and record that in notes.

## Implementation Plan

1. Confirm task dependencies are complete.
2. Run focused CCXT source tests.
3. Run focused MCP tests.
4. Run full fast checks.
5. Run focused dbt checks.
6. Run the live CCXT Binance `BTC/USDT` ticker and order book smoke.
7. Inspect raw, staging, mart, and MCP evidence.
8. Record exact command outcomes in this task.

## Acceptance Criteria

- [x] Focused CCXT source tests pass.
- [x] Focused MCP tests pass.
- [x] Fast local checks pass.
- [x] Focused dbt checks pass or an environment blocker is documented.
- [x] Live CCXT Binance `BTC/USDT` ticker smoke passes.
- [x] Live CCXT Binance `BTC/USDT` order book smoke passes.
- [x] Raw CCXT rows exist for both entities.
- [x] Staging CCXT rows exist for both entities.
- [x] Mart CCXT rows exist for both entities.
- [x] MCP allowlist access works for both CCXT marts.
- [x] Task notes contain exact verification commands and results.
- [x] No production reconciliation command is run.

## Notes

- Focused CCXT source tests:
  - `./.venv/bin/pytest tests/unit/sources/ccxt/test_extractor.py tests/unit/sources/ccxt/test_runner.py tests/unit/sources/ccxt/test_cli.py tests/unit/test_top_level_cli.py -q`
    -> `13 passed in 0.19s`
- Focused MCP tests:
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
    -> `48 passed in 0.39s`
- Fast local checks:
  - `./.venv/bin/ruff check .`
    -> `All checks passed!`
  - `./.venv/bin/ruff format --check .`
    -> `116 files already formatted`
  - `./.venv/bin/python -m mypy`
    -> `Success: no issues found in 104 source files`
  - `./.venv/bin/pytest tests/unit -q`
    -> `157 passed in 1.56s`
- Fast-check fix on July 28, 2026:
  - the first `mypy` and `pytest tests/unit` runs failed because the new
    `tests/unit/sources/ccxt/` files collided with same-basename test modules
    under non-package source test folders.
  - fix: added package markers:
    - `tests/unit/sources/__init__.py`
    - `tests/unit/sources/ccxt/__init__.py`
    - `tests/unit/sources/coingecko/__init__.py`
    - `tests/unit/sources/csv_import/__init__.py`
  - rerunning the fast checks after that fix succeeded.
- Focused dbt verification:
  - `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
    -> `PASS=4`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
    -> `PASS=4`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
    -> `PASS=24`
  - sandboxed dbt still cannot connect to local Postgres on `localhost:5432`, so
    the seed/run/test commands were rerun outside the sandbox as allowed by the
    task notes.
- Live CCXT Binance smoke:
  - `./.venv/bin/felts ccxt run --entities ticker order_book`
    -> `source=ccxt`
    -> `entity=ticker extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`
    -> `entity=order_book extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`
- Raw, staging, and mart evidence from direct Postgres inspection on July 28, 2026:
  - `raw_ticker_count [(3,)]`
  - `raw_order_book_count [(3,)]`
  - `stg_ticker_count [(3,)]`
  - `stg_order_book_count [(3,)]`
  - `mart_ticker_count [(2,)]`
  - `mart_order_book_count [(2,)]`
  - latest ticker row:
    - `('binance', 'BTC/USDT', 63453.26, 63453.26, 63453.27, 2026-07-28 12:45:21.001000+00:00)`
  - latest order-book row:
    - `('binance', 'BTC/USDT', 63453.26, 63453.27, 0.01, 63453.265000000000, 20, 20, 2026-07-28 12:45:21.911955+00:00)`
  - note: raw and staging have three rows per entity, while marts have two rows
    because the mart grain deduplicates on `exchange_id, symbol, observed_at`.
- MCP access evidence:
  - `./.venv/bin/python - <<'PY' ... validate_query('select observed_at, last_price from ccxt.mart_ccxt__tickers limit 5') ... PY`
    -> `SELECT observed_at, last_price FROM ccxt.mart_ccxt__tickers LIMIT 5`
  - `./.venv/bin/python - <<'PY' ... validate_query('select observed_at, best_bid, best_ask from ccxt.mart_ccxt__order_book_snapshots limit 5') ... PY`
    -> `SELECT observed_at, best_bid, best_ask FROM ccxt.mart_ccxt__order_book_snapshots LIMIT 5`
- No production reconciliation command was run. `scripts/update-prod-data-access.sh`
  was not executed.
- Reviewer verification on 2026-07-28:
  - Focused CCXT source tests:
    - `./.venv/bin/pytest tests/unit/sources/ccxt/test_extractor.py tests/unit/sources/ccxt/test_runner.py tests/unit/sources/ccxt/test_cli.py tests/unit/test_top_level_cli.py -q`
      -> `13 passed in 0.16s`
  - Focused MCP tests:
    - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
      -> `48 passed in 0.34s`
  - Fast local checks:
    - `./.venv/bin/ruff check .`
      -> `All checks passed!`
    - `./.venv/bin/ruff format --check .`
      -> `116 files already formatted`
    - `./.venv/bin/python -m mypy`
      -> `Success: no issues found in 104 source files`
    - `./.venv/bin/pytest tests/unit -q`
      -> `157 passed in 1.49s`
  - Focused dbt checks rerun unsandboxed against local Postgres:
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
      -> `PASS=4`
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
      -> `PASS=4`
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots`
      -> `PASS=24`
  - Live CCXT Binance smoke rerun unsandboxed:
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/felts ccxt run --entities ticker order_book`
      -> `entity=ticker extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`
      -> `entity=order_book extracted=1 inserted=1 skipped_duplicate=0 invalid=0 failed=0`
  - Direct Postgres inspection on July 28, 2026 after the reviewer smoke run:
    - counts:
      - `raw_ticker_count=4`
      - `raw_order_book_count=4`
      - `stg_ticker_count=4`
      - `stg_order_book_count=4`
      - `mart_ticker_count=3`
      - `mart_order_book_count=3`
    - latest ticker mart row:
      - `('binance', 'BTC/USDT', 63166.0, 63166.0, 63166.01, 2026-07-28 14:03:04.010000+00:00)`
    - latest order-book mart row:
      - `('binance', 'BTC/USDT', 63166.0, 63166.01, 0.01, 63166.005000000000, 20, 20, 2026-07-28 14:03:04.298325+00:00)`
    - note: counts are one higher than the worker’s earlier sample because the
      reviewer reran the live smoke and inserted another snapshot for each
      entity on July 28, 2026.
  - MCP access rerun:
    - `validate_query('select observed_at, last_price from ccxt.mart_ccxt__tickers limit 5')`
      -> `SELECT observed_at, last_price FROM ccxt.mart_ccxt__tickers LIMIT 5`
    - `validate_query('select observed_at, best_bid, best_ask from ccxt.mart_ccxt__order_book_snapshots limit 5')`
      -> `SELECT observed_at, best_bid, best_ask FROM ccxt.mart_ccxt__order_book_snapshots LIMIT 5`
  - No review findings.

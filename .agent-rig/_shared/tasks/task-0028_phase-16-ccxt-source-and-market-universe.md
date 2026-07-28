---
id: task-0028
title: "Phase 16: CCXT source and market universe"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-28
priority: normal
parent: ""
depends_on: []
---










# Task

## Context

Phase 16 adds the first CCXT public exchange market-data vertical slice.

Source of truth:

- `docs/phases/phase_16_ccxt_exchange_market_snapshots.md`

## Goal

Add the CCXT dependency, committed market universe, source extraction, raw load,
and CLI path for Binance `BTC/USDT` ticker and top-20 order book snapshots.

## Scope

- Move `ccxt` from the optional finance dependency group into main dependencies.
- Add a committed CCXT market universe with active Binance `BTC/USDT` and order
  book limit 20.
- Add a source-owned CCXT package following existing source runner/raw writer
  patterns.
- Add separate entities:
  - `ticker`
  - `order_book`
- Implement ticker capture with `fetch_ticker("BTC/USDT")`.
- Implement order book capture with `fetch_order_book("BTC/USDT", limit=20)`.
- Use provider timestamp for `observed_at` when available, otherwise extraction
  time.
- Build `source_record_id` as:

  ```text
  <entity>|<exchange_id>|<symbol>|<observed_at>
  ```

- Preserve successful entity records even when another requested entity fails,
  but fail the overall run if any requested entity fails.
- Register the CLI path:

  ```bash
  ./.venv/bin/felts ccxt run --entities ticker order_book
  ```

## Planner Notes

Do not add a CCXT cron, Prefect schedule, exchange credentials, private account
APIs, internal asset mapping, or internal exchange market model in this task.

The required exchange target is CCXT `binance`; do not silently switch to
`binanceus` or another exchange if access fails.

## Implementation Plan

1. Update dependencies and lock files consistently with the repo tooling.
2. Add the committed CCXT market universe seed/config.
3. Implement the CCXT extractor/client using public CCXT methods only.
4. Implement the CCXT runner and raw payload construction for both entities.
5. Register the CCXT CLI command.
6. Add focused unit tests for dependency-visible imports, market universe loading,
   entity extraction shape, timestamp fallback, source record IDs, and partial
   failure behavior.
7. Run focused unit tests and record results in `## Notes`.

## Acceptance Criteria

- [x] `ccxt` is a main dependency, not only an optional finance dependency.
- [x] The committed market universe includes active Binance `BTC/USDT` with
      order book limit 20.
- [x] Ticker extraction uses `fetch_ticker`.
- [x] Order book extraction uses `fetch_order_book` with limit 20.
- [x] Raw records are written with source `ccxt`.
- [x] Entities remain distinct as `ticker` and `order_book`.
- [x] `observed_at` uses provider timestamp when present and extraction time
      when absent.
- [x] `source_record_id` follows
      `<entity>|<exchange_id>|<symbol>|<observed_at>`.
- [x] Successful entity rows are preserved if another requested entity fails.
- [x] The overall command or runner result fails when any requested entity fails.
- [x] Focused verification results are recorded in `## Notes`.

## Notes

- Implemented a new `src/felts/sources/ccxt/` package with provider-native
  `ticker` and `order_book` entities, a committed market-universe loader, raw
  payload schemas, runner partial-failure handling, and CLI registration at
  `./.venv/bin/felts ccxt run --entities ticker order_book`.
- Moved `ccxt` into main project dependencies in `pyproject.toml`, regenerated
  `uv.lock`, and synced the local `.venv` with `uv sync --all-groups` so the
  command can import `ccxt` from the checked-out environment.
- Added the committed seed/config at
  `transforms/seeds/ccxt/ccxt_market_universe.csv` and configured CCXT seeds in
  `transforms/dbt_project.yml`.
- Focused verification:
  - `./.venv/bin/ruff check src/felts/sources/ccxt tests/unit/sources/ccxt src/felts/cli.py tests/unit/test_top_level_cli.py`
    -> `All checks passed!`
  - `./.venv/bin/ruff format --check src/felts/sources/ccxt tests/unit/sources/ccxt src/felts/cli.py tests/unit/test_top_level_cli.py`
    -> `11 files already formatted`
  - `./.venv/bin/python -m mypy src/felts/sources/ccxt src/felts/cli.py tests/unit/sources/ccxt tests/unit/test_top_level_cli.py`
    -> `Success: no issues found in 11 source files`
  - `./.venv/bin/pytest tests/unit/sources/ccxt/test_extractor.py tests/unit/sources/ccxt/test_runner.py tests/unit/sources/ccxt/test_cli.py tests/unit/test_top_level_cli.py -q`
    -> `11 passed in 2.38s`
  - `./.venv/bin/python -c 'import psycopg, sqlglot, ccxt; print("ok")'`
    -> `ok`
- Reviewer finding on 2026-07-28:
  - `src/felts/sources/ccxt/extractor.py:61` and `src/felts/sources/ccxt/extractor.py:98`
    call the CCXT client directly without normalizing provider exceptions into
    `ExtractionError`.
  - `src/felts/sources/ccxt/runner.py:65-69` only converts `ExtractionError`
    into a failed entity summary, so a normal CCXT/provider exception still
    aborts the full run and prevents later entities from running.
  - Repro:
    - `./.venv/bin/python - <<'PY' ... run_ccxt_source(entities=['ticker', 'order_book'], extractor=extractor, writer=writer) ... PY`
      -> `RuntimeError: provider boom`
  - This misses the task contract: preserve successful entity rows when another
    requested entity fails, while still failing the overall run.
  - Fix direction: wrap provider fetch/parsing failures at the extractor
    boundary as `ExtractionError`, then add a focused unit test using a client
    that raises a non-`ExtractionError` provider exception.
- Follow-up fix on 2026-07-28:
  - Wrapped `fetch_ticker` and `fetch_order_book` provider failures in
    `src/felts/sources/ccxt/extractor.py` so non-CCXT exceptions are normalized
    into `ExtractionError` at the extractor boundary.
  - Added focused regression coverage for:
    - extractor normalization of a raw `RuntimeError("provider boom")`
    - runner preservation of inserted ticker rows while the later order-book
      entity fails through the real extractor path
  - Follow-up verification:
    - `./.venv/bin/ruff check src/felts/sources/ccxt tests/unit/sources/ccxt`
      -> `All checks passed!`
    - `./.venv/bin/ruff format --check src/felts/sources/ccxt tests/unit/sources/ccxt`
      -> `9 files already formatted`
    - `./.venv/bin/python -m mypy src/felts/sources/ccxt tests/unit/sources/ccxt`
      -> `Success: no issues found in 9 source files`
    - `./.venv/bin/pytest tests/unit/sources/ccxt/test_extractor.py tests/unit/sources/ccxt/test_runner.py tests/unit/sources/ccxt/test_cli.py tests/unit/test_top_level_cli.py -q`
      -> `13 passed in 0.14s`
- Reviewer verification on 2026-07-28:
  - Re-ran `./.venv/bin/pytest tests/unit/sources/ccxt/test_extractor.py tests/unit/sources/ccxt/test_runner.py tests/unit/sources/ccxt/test_cli.py tests/unit/test_top_level_cli.py -q`
    -> `13 passed in 0.14s`
  - Re-ran the July 28, 2026 provider-failure repro through the real extractor
    and runner path with a client that raises `RuntimeError("provider boom")`
    from `fetch_order_book`.
    - Result:
      `{'entities': [('ticker', 1, 0), ('order_book', 0, 1)], 'failed_count': 1}`
  - The previous contract gap is fixed: successful ticker rows are preserved,
    the failing order-book entity is summarized as failed, and the overall run
    still reports failure.

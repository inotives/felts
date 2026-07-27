---
id: task-0027
title: "Phase 15: verification and close-out"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on:
  - task-0026
---




# Task

## Context

Tasks 0024 through 0026 implement the Phase 15 CoinGecko public OHLC rollup fix.

Source of truth:

- `docs/phases/phase_15_coingecko_public_ohlc_rollup_fix.md`

## Goal

Run final local verification for Phase 15, including the required live
`coins_ohlc` smoke check.

## Scope

- Run fast checks:
  - `./.venv/bin/ruff check .`
  - `./.venv/bin/ruff format --check .`
  - `./.venv/bin/python -m mypy`
  - `./.venv/bin/pytest tests/unit`
- Run focused CoinGecko and MCP tests.
- Run dbt checks:
  - `dbt seed`
  - `dbt run --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `dbt test --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
- Run required live smoke:
  - `./.venv/bin/felts coingecko run --entities coins_ohlc`
- Record exact command evidence in `## Notes`.
- Do not run `scripts/update-prod-data-access.sh` against production.
- Do not archive the Phase 15 doc unless the human explicitly asks after merge.

## Planner Notes

If sandboxed dbt cannot connect to local Postgres on `localhost:5432`, rerun dbt
outside the sandbox and record that in notes.

The live smoke check is required because Phase 15 exists to fix a live provider
request failure.

## Implementation Plan

1. Confirm task dependencies are complete.
2. Run focused unit tests for source request params, dbt-facing contracts, and
   MCP allowlist behavior.
3. Run full fast checks.
4. Run focused dbt checks.
5. Run the live `coins_ohlc` source smoke.
6. Record exact command outcomes in this task.

## Acceptance Criteria

- [ ] Focused CoinGecko source tests pass.
- [ ] Focused MCP tests pass.
- [ ] Fast local checks pass.
- [ ] Focused dbt checks pass or an environment blocker is documented.
- [ ] Live `coins_ohlc` smoke passes.
- [ ] Task notes contain exact verification commands and results.
- [ ] No production reconciliation command is run.

## Notes

- Focused CoinGecko source verification:
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
  - `31 passed in 1.20s`
- Focused MCP verification:
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
  - `40 passed in 0.30s`
- Fast local checks:
  - `./.venv/bin/ruff check .`
  - `All checks passed!`
  - `./.venv/bin/ruff format --check .`
  - Initial result: `Would reformat: tests/unit/sources/coingecko/test_extractor.py` and `tests/unit/sources/coingecko/test_runner.py`
  - Fixed with: `./.venv/bin/ruff format tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py`
  - Recheck result: `103 files already formatted`
  - `./.venv/bin/python -m mypy`
  - `Success: no issues found in 91 source files`
  - `./.venv/bin/pytest tests/unit`
  - `137 passed in 1.24s`
- Focused dbt checks against local Postgres were run outside the sandbox because
  they require localhost database access:
  - `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
  - `PASS=3`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `PASS=6`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `PASS=61`
- Required live public API smoke:
  - `./.venv/bin/felts coingecko run --entities coins_ohlc`
  - Result:
    - `source=coingecko`
    - `entity=coins_ohlc extracted=540 inserted=540 skipped_duplicate=0 invalid=0 failed=0`
- No production reconciliation command was run.
- Reviewer verification on Monday, July 27, 2026:
  - Focused CoinGecko source tests:
    - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
    - `31 passed in 1.12s`
  - Focused MCP tests:
    - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
    - `40 passed in 0.26s`
  - Fast local checks:
    - `./.venv/bin/ruff check .`
    - `All checks passed!`
    - `./.venv/bin/ruff format --check .`
    - `103 files already formatted`
    - `./.venv/bin/python -m mypy`
    - `Success: no issues found in 91 source files`
    - `./.venv/bin/pytest tests/unit`
    - `137 passed in 1.23s`
  - Focused dbt checks:
    - sandboxed `dbt seed` failed on localhost Postgres permission denial, then reran unsandboxed per task instructions
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
    - `PASS=3`
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    - `PASS=6`
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    - `PASS=61`
  - Live public API smoke:
    - sandboxed run failed on DNS/network resolution, then reran unsandboxed
    - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/felts coingecko run --entities coins_ohlc`
    - `source=coingecko entity=coins_ohlc extracted=540 inserted=1 skipped_duplicate=539 invalid=0 failed=0`
    - The reduced insert count versus the worker run is expected because prior
      reviewer/worker smoke runs had already loaded most of the same raw rows;
      the live provider path itself succeeded.

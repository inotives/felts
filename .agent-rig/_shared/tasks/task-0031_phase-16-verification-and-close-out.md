---
id: task-0031
title: "Phase 16: verification and close-out"
type: task
status: pending
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
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

- [ ] Focused CCXT source tests pass.
- [ ] Focused MCP tests pass.
- [ ] Fast local checks pass.
- [ ] Focused dbt checks pass or an environment blocker is documented.
- [ ] Live CCXT Binance `BTC/USDT` ticker smoke passes.
- [ ] Live CCXT Binance `BTC/USDT` order book smoke passes.
- [ ] Raw CCXT rows exist for both entities.
- [ ] Staging CCXT rows exist for both entities.
- [ ] Mart CCXT rows exist for both entities.
- [ ] MCP allowlist access works for both CCXT marts.
- [ ] Task notes contain exact verification commands and results.
- [ ] No production reconciliation command is run.

## Notes

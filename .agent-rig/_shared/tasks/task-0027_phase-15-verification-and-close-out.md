---
id: task-0027
title: "Phase 15: verification and close-out"
type: task
status: blocked
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

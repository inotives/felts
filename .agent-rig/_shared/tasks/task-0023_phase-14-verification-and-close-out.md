---
id: task-0023
title: "Phase 14: verification and close-out"
type: task
status: blocked
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on:
  - task-0022
---

# Task

## Context

Tasks 0020 through 0022 implement Phase 14 CoinGecko daily market metrics,
derived OHLCV, scheduling, and MCP exposure.

Source of truth:

- `docs/phases/phase_14_coingecko_daily_market_metrics_and_ohlcv.md`

## Goal

Run final local verification for Phase 14 and update implemented-state docs.

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
- Update implemented-state docs after checks pass.
- Record exact command evidence in `## Notes`.
- Do not run `scripts/update-prod-data-access.sh` against production.
- Do not archive the Phase 14 doc unless the human explicitly asks after merge.

## Planner Notes

Production access reconciliation remains an operator step after deployment and dbt
have created the Phase 14 marts in production.

## Implementation Plan

1. Confirm task dependencies are complete.
2. Run focused unit tests for CoinGecko market chart, OHLC daily interval,
   schedules, event selectors, and MCP access.
3. Run full fast checks.
4. Run focused dbt checks.
5. Update README/project specs/current docs to say Felts is implemented through
   Phase 14 and includes daily CoinGecko market metrics plus derived OHLCV.
6. Record exact command outcomes in this task.

## Acceptance Criteria

- [ ] Focused CoinGecko source tests pass.
- [ ] Focused MCP tests pass.
- [ ] Fast local checks pass.
- [ ] Focused dbt checks pass or an environment blocker is documented.
- [ ] Implemented-state docs describe Phase 14.
- [ ] Task notes contain exact verification commands and results.
- [ ] No production reconciliation command is run.

## Notes


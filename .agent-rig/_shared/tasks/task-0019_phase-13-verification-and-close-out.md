---
id: task-0019
title: "Phase 13: verification and close-out"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-25
priority: normal
parent: ""
depends_on:
  - task-0018
---

# Task

## Context

Tasks 0016 through 0018 implement Phase 13 CoinGecko OHLC capture, modeling, and
MCP exposure.

Source of truth:

- `docs/phases/phase_13_coingecko_ohlc_capture.md`

## Goal

Run final local verification for Phase 13 and update implemented-state docs.

## Scope

- Run fast checks:
  - `./.venv/bin/ruff check .`
  - `./.venv/bin/ruff format --check .`
  - `./.venv/bin/python -m mypy`
  - `./.venv/bin/pytest tests/unit`
- Run focused CoinGecko/MCP tests.
- Run dbt checks:
  - `dbt seed`
  - `dbt run --select stg_coingecko__coins_ohlc+`
  - `dbt test --select stg_coingecko__coins_ohlc+`
- Update implemented-state docs after checks pass.
- Record exact command evidence in `## Notes`.
- Do not run `scripts/update-prod-data-access.sh` against production.
- Do not archive the Phase 13 doc unless the human explicitly asks after merge.

## Planner Notes

Production access reconciliation remains an operator step after deployment and dbt
have created the OHLC mart in production.

## Implementation Plan

1. Confirm task dependencies are complete.
2. Run focused unit tests for CoinGecko OHLC and MCP access.
3. Run full fast checks.
4. Run focused dbt checks.
5. Update README/project specs/current docs to say Felts is implemented through
   Phase 13 and has scheduled CoinGecko OHLC capture.
6. Record exact command outcomes in this task.

## Acceptance Criteria

- [ ] Focused CoinGecko OHLC tests pass.
- [ ] Focused MCP tests pass.
- [ ] Fast local checks pass.
- [ ] Focused dbt checks pass or an environment blocker is documented.
- [ ] Implemented-state docs describe Phase 13.
- [ ] Task notes contain exact verification commands and results.
- [ ] No production reconciliation command is run.

## Notes

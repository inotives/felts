---
id: task-0026
title: "Phase 15: MCP and docs alignment"
type: task
status: blocked
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on:
  - task-0025
---

# Task

## Context

Task 0025 changes the OHLC and OHLCV marts to daily rollup semantics while keeping
their public names.

Source of truth:

- `docs/phases/phase_15_coingecko_public_ohlc_rollup_fix.md`

## Goal

Align MCP tests/docs and project docs with the Phase 15 public OHLC rollup
contract without expanding the MCP allowlist.

## Scope

- Keep `settings/felts-prod-data-views.txt` unchanged.
- Confirm the allowlist does not include:
  - `coingecko.int_coingecko__coin_ohlc_daily_rollups`
  - raw OHLC relations
  - staging OHLC relations
- Update `tests/unit/test_prod_data_mcp.py` only if expected mart semantics or
  allowlist assertions need adjustment.
- Update `docs/mcp/felts-prod-data.md` so the OHLC mart is described as daily
  rollup output.
- Update README/project specs/current docs to describe:
  - public-compatible 30-day OHLC capture;
  - provider 4-hour staging;
  - dbt-derived daily OHLC rollups;
  - daily OHLCV built from rollup OHLC plus market-chart metrics.
- Do not run production access reconciliation.

## Planner Notes

This task should not expose intermediate models. Keep mart-first MCP access.

## Implementation Plan

1. Check the MCP allowlist remains unchanged.
2. Update focused MCP tests if needed to assert no intermediate exposure.
3. Update MCP and implemented-state docs.
4. Run focused MCP/docs-adjacent unit tests.

## Acceptance Criteria

- [ ] MCP allowlist still contains the existing OHLC and OHLCV marts.
- [ ] MCP allowlist does not expose intermediate, staging, or raw OHLC relations.
- [ ] MCP docs describe the OHLC mart as daily rollup candles.
- [ ] Implemented-state docs describe the Phase 15 public API fix.
- [ ] No production reconciliation command is run.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

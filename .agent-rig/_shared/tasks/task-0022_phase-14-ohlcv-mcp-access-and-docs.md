---
id: task-0022
title: "Phase 14: OHLCV MCP access and docs"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on:
  - task-0021
---


# Task

## Context

Task 0021 adds the CoinGecko daily market metrics mart and derived OHLCV mart.
Phase 14 requires both marts to be available through the existing mart-first MCP
access path.

Source of truth:

- `docs/phases/phase_14_coingecko_daily_market_metrics_and_ohlcv.md`

## Goal

Expose the Phase 14 marts through the committed MCP allowlist and update access
docs/tests.

## Scope

- Add these relations to `settings/felts-prod-data-views.txt`:
  - `coingecko.mart_coingecko__coin_daily_market_metrics`
  - `coingecko.mart_coingecko__coin_ohlcv_daily`
- Update `tests/unit/test_prod_data_mcp.py`.
- Update `docs/mcp/felts-prod-data.md`.
- Keep schema-qualified allowlist entries only.
- Do not expose raw or staging market-chart relations.
- Do not run production access reconciliation.

## Planner Notes

This is an access-list and docs/test task only. Do not change the MCP SQL safety
policy unless a focused test exposes a current bug.

## Implementation Plan

1. Add the two Phase 14 marts to the committed allowlist.
2. Update allowlist assertions and accepted query coverage.
3. Update docs so both marts appear in the preferred mart surface.
4. Run focused MCP tests.

## Acceptance Criteria

- [ ] The allowlist contains
      `coingecko.mart_coingecko__coin_daily_market_metrics`.
- [ ] The allowlist contains `coingecko.mart_coingecko__coin_ohlcv_daily`.
- [ ] No raw or staging market-chart relation is allowlisted.
- [ ] MCP tests accept bounded selects from both new marts.
- [ ] MCP docs list both new marts in the mart-first surface.
- [ ] No production reconciliation command is run.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

- Added Phase 14 marts to the committed schema-qualified MCP allowlist:
  `coingecko.mart_coingecko__coin_daily_market_metrics` and
  `coingecko.mart_coingecko__coin_ohlcv_daily`.
- Updated `tests/unit/test_prod_data_mcp.py` to:
  - assert both new marts are in the committed allowlist
  - accept bounded selects from both new marts
  - reject `coingecko.stg_coingecko__coins_market_chart`
  - cover `describe_allowed_view` for both new marts
- Updated `docs/mcp/felts-prod-data.md` so both Phase 14 marts appear in the
  preferred mart-first surface.
- No production reconciliation command was run.
- Verification:
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
    -> `37 passed in 0.23s`
  - `./.venv/bin/ruff check tests/unit/test_prod_data_mcp.py`
    -> `All checks passed!`
  - `./.venv/bin/ruff format --check tests/unit/test_prod_data_mcp.py`
    -> `1 file already formatted`

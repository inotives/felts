---
id: task-0018
title: "Phase 13: OHLC MCP access and docs"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-25
priority: normal
parent: ""
depends_on:
  - task-0017
---

# Task

## Context

Task 0017 adds the CoinGecko OHLC mart. Phase 13 requires that mart to be available
through the existing mart-first MCP access path.

Source of truth:

- `docs/phases/phase_13_coingecko_ohlc_capture.md`

## Goal

Expose `coingecko.mart_coingecko__coin_ohlc_candles` through the committed MCP
allowlist and update access docs/tests.

## Scope

- Add `coingecko.mart_coingecko__coin_ohlc_candles` to
  `settings/felts-prod-data-views.txt`.
- Update `tests/unit/test_prod_data_mcp.py`.
- Update `docs/mcp/felts-prod-data.md`.
- Keep schema-qualified allowlist entries only.
- Do not expose raw or staging OHLC relations.
- Do not run production access reconciliation.

## Planner Notes

This is an access-list and docs/test task only. Do not change the MCP SQL safety
policy unless a focused test exposes a current bug.

## Implementation Plan

1. Add the OHLC mart to the committed allowlist.
2. Update allowlist assertions and accepted query coverage.
3. Update docs so the new CoinGecko OHLC mart appears in the preferred mart surface.
4. Run focused MCP tests.

## Acceptance Criteria

- [ ] The allowlist contains `coingecko.mart_coingecko__coin_ohlc_candles`.
- [ ] No raw or staging OHLC relation is allowlisted.
- [ ] MCP tests accept a bounded select from the OHLC mart.
- [ ] MCP docs list the OHLC mart in the mart-first surface.
- [ ] No production reconciliation command is run.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

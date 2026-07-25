---
id: task-0013
title: "Phase 12: mart-first MCP allowlist"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-25
priority: normal
parent: ""
depends_on: []
---







# Task

## Context

Phase 12 refreshes Felts production analytical access so MCP clients use the Phase
11 mart surface instead of older staging relations.

Source of truth:

- `docs/phases/phase_12_analytical_access_refresh.md`

## Goal

Update the committed production data allowlist to expose Phase 11 marts and remove
staging entries that now have mart replacements.

## Scope

- Update `settings/felts-prod-data-views.txt`.
- Allowlist these mart relations:
  - `coingecko.mart_coingecko__asset_platforms`
  - `coingecko.mart_coingecko__coins`
  - `coingecko.mart_coingecko__coin_market_snapshots`
  - `coingecko.mart_coingecko__global_market_snapshots`
  - `coingecko.mart_coingecko__global_defi_snapshots`
  - `alphavantage.mart_alphavantage__daily_prices`
  - `csv_import.mart_csv_import__ohlcv`
  - `csv_import.mart_csv_import__fred_observations`
  - `felts.mart_felts__assets`
  - `felts.mart_felts__asset_platforms`
  - `felts.mart_felts__asset_provider_mappings`
- Remove staging entries that have mart replacements.
- Keep schema-qualified entries only.
- Do not add raw tables.
- Do not add report/query surfaces.

## Planner Notes

This task is intentionally a policy-list update. Do not change MCP SQL safety behavior
unless an existing test exposes a current bug.

## Implementation Plan

1. Replace the allowlist with the Phase 12 mart-first set.
2. Keep the file sorted or grouped in a readable source/schema order.
3. Run the focused allowlist test if available, or record that tests are updated in
   the next task.

## Acceptance Criteria

- [ ] The allowlist contains all Phase 12 mart relations.
- [ ] The allowlist no longer contains replaced staging relations.
- [ ] All allowlist entries are schema-qualified.
- [ ] No raw tables are allowlisted.
- [ ] No SQL policy behavior changes are introduced.
- [ ] Notes record the exact allowlist shape or focused verification.

## Notes

- Reviewer return on 2026-07-25: the committed allowlist matches the Phase 12 mart
  contract, but focused MCP tests are now stale and fail against the new list.
  `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q` failed with 2 failures:
  `test_load_allowed_views_reads_committed_allowlist` still expects the removed
  staging entries from `tests/unit/test_prod_data_mcp.py:23-35`, and
  `test_validate_query_allows_unbounded_aggregate` still asserts
  `public.stg_alphavantage__time_series_daily` is allowlisted from
  `tests/unit/test_prod_data_mcp.py:44-47`. `./.venv/bin/pytest
  tests/unit/test_deploy_script_guards.py -q` still passes (7 passed). Return this
  task only after the allowlist change no longer leaves focused MCP coverage red or
  after coordinating the dependency boundary with Task 0014 explicitly.
- Updated `settings/felts-prod-data-views.txt` to the Phase 12 mart-first set:
  `alphavantage.mart_alphavantage__daily_prices`,
  `coingecko.mart_coingecko__asset_platforms`,
  `coingecko.mart_coingecko__coin_market_snapshots`,
  `coingecko.mart_coingecko__coins`,
  `coingecko.mart_coingecko__global_defi_snapshots`,
  `coingecko.mart_coingecko__global_market_snapshots`,
  `csv_import.mart_csv_import__fred_observations`,
  `csv_import.mart_csv_import__ohlcv`,
  `felts.mart_felts__asset_platforms`,
  `felts.mart_felts__asset_provider_mappings`,
  `felts.mart_felts__assets`.
- Removed replaced staging entries for Alpha Vantage, CoinGecko global/markets/platforms,
  and CSV import relations.
- Follow-up fix on 2026-07-25: updated `tests/unit/test_prod_data_mcp.py` so the
  committed allowlist assertion and aggregate acceptance case match the Phase 12
  mart-first surface.
- Verification on 2026-07-25:
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q` -> `16 passed in 0.22s`
  - `./.venv/bin/pytest tests/unit/test_deploy_script_guards.py -q` -> `7 passed in 0.01s`

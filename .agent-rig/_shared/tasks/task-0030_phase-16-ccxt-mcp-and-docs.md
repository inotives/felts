---
id: task-0030
title: "Phase 16: CCXT MCP and docs alignment"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-28
priority: normal
parent: ""
depends_on:
  - task-0029
---







# Task

## Context

Task 0029 adds provider-native CCXT marts. Phase 16 requires those marts to be
available through the existing mart-first, schema-qualified MCP access policy.

Source of truth:

- `docs/phases/phase_16_ccxt_exchange_market_snapshots.md`

## Goal

Expose only the new CCXT marts through MCP and align tests/docs with the Phase 16
access surface.

## Scope

- Add these schema-qualified marts to `settings/felts-prod-data-views.txt`:
  - `ccxt.mart_ccxt__tickers`
  - `ccxt.mart_ccxt__order_book_snapshots`
- Update MCP unit tests so the committed allowlist includes the two CCXT marts.
- Add policy coverage that CCXT raw and staging relations are rejected.
- Update `docs/mcp/felts-prod-data.md` to describe the CCXT mart access surface.
- Update project docs/current implemented-state docs to mention the Phase 16
  CCXT source, provider-native marts, and manual-only capture.

## Planner Notes

Do not expose CCXT raw or staging relations through MCP.

Do not run `scripts/update-prod-data-access.sh` against production.

## Implementation Plan

1. Update the committed MCP allowlist with the two CCXT marts only.
2. Update MCP allowlist and policy tests.
3. Update MCP and project docs for the implemented CCXT analytical surface.
4. Run focused MCP tests and record results in `## Notes`.

## Acceptance Criteria

- [x] The committed allowlist contains `ccxt.mart_ccxt__tickers`.
- [x] The committed allowlist contains
      `ccxt.mart_ccxt__order_book_snapshots`.
- [x] The committed allowlist contains no CCXT raw relations.
- [x] The committed allowlist contains no CCXT staging relations.
- [x] MCP tests accept schema-qualified selects from both CCXT marts.
- [x] MCP tests reject CCXT raw and staging relation access.
- [x] MCP docs describe the CCXT marts as manual public exchange snapshots.
- [x] No production reconciliation command is run.
- [x] Focused verification results are recorded in `## Notes`.

## Notes

- Added the two schema-qualified CCXT marts to
  `settings/felts-prod-data-views.txt`:
  - `ccxt.mart_ccxt__order_book_snapshots`
  - `ccxt.mart_ccxt__tickers`
- Updated `tests/unit/test_prod_data_mcp.py` so MCP policy coverage now:
  - accepts schema-qualified selects from both CCXT marts
  - rejects CCXT raw relations
  - rejects CCXT staging relations
  - resolves schema-qualified metadata lookups for the two CCXT marts
  - loads the new CCXT dbt mart descriptions
- Updated docs:
  - `docs/mcp/felts-prod-data.md`
  - `README.md`
  - `docs/project_specs.md`
- Focused verification:
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
    -> `48 passed in 0.35s`
  - `./.venv/bin/ruff check tests/unit/test_prod_data_mcp.py`
    -> `All checks passed!`
  - `./.venv/bin/ruff format --check tests/unit/test_prod_data_mcp.py`
    -> `1 file already formatted`
- No production reconciliation command was run. I did not run
  `scripts/update-prod-data-access.sh`.
- Reviewer verification on 2026-07-28:
  - Re-ran `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
    -> `48 passed in 0.35s`
  - Direct committed allowlist check on `settings/felts-prod-data-views.txt`:
    - total entries: `16`
    - CCXT entries:
      - `ccxt.mart_ccxt__order_book_snapshots`
      - `ccxt.mart_ccxt__tickers`
    - blocked CCXT entries found: `[]`
  - Verified the MCP/docs diff keeps the Phase 16 surface mart-first and
    schema-qualified:
    - MCP tests allow both CCXT marts
    - MCP tests reject `ccxt.raw_ticker`, `ccxt.raw_order_book`,
      `ccxt.stg_ccxt__tickers`, and `ccxt.stg_ccxt__order_books`
    - docs describe the CCXT marts as manual public exchange snapshots
  - No review findings.

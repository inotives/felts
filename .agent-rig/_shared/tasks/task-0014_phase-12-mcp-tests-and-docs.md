---
id: task-0014
title: "Phase 12: MCP tests and docs"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-25
priority: normal
parent: ""
depends_on:
  - task-0013
---





# Task

## Context

Task 0013 updates the mart-first MCP allowlist. This task updates tests and docs so
the access contract is explicit.

Source of truth:

- `docs/phases/phase_12_analytical_access_refresh.md`

## Goal

Extend the MCP tests and documentation for the Phase 12 mart-first access contract.

## Scope

- Update `tests/unit/test_prod_data_mcp.py`.
- Update `docs/mcp/felts-prod-data.md`.
- Tests should cover:
  - committed allowlist contents;
  - `validate_query` accepting new schema-qualified mart names;
  - `describe_allowed_view` for `felts`, `alphavantage`, and `csv_import` schemas;
  - rejection of removed staging relations.
- Docs should explain:
  - marts are the preferred MCP access layer;
  - clients must use exact `schema.relation` names;
  - production access reconciliation is still done through
    `scripts/update-prod-data-access.sh`.
- Do not add saved report examples or a query command surface.

## Planner Notes

Keep examples minimal and policy-focused. This phase is not a report-building phase.

## Implementation Plan

1. Update the unit tests to match the new allowlist.
2. Add focused tests for accepted new mart queries and rejected replaced staging
   queries.
3. Update MCP docs with the mart-first contract and operator reconciliation note.
4. Run focused unit tests for `test_prod_data_mcp.py`.

## Acceptance Criteria

- [ ] Tests assert the committed allowlist contains the Phase 12 mart set.
- [ ] Tests prove new mart relations are accepted by `validate_query`.
- [ ] Tests prove removed staging relations are rejected.
- [ ] Tests cover schema-qualified describe behavior for non-`coingecko` schemas.
- [ ] MCP docs describe mart-first access and the safe reconciliation command.
- [ ] No report/query surface is added.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

- Updated `tests/unit/test_prod_data_mcp.py` for the Phase 12 mart-first contract:
  - kept the committed allowlist assertion aligned with `settings/felts-prod-data-views.txt`
  - added accepted `validate_query` coverage for `alphavantage`, `csv_import`, and
    `felts` mart relations
  - added rejection coverage for removed staging relations replaced by marts
  - expanded `describe_allowed_view` coverage to schema-qualified lookups for
    `coingecko`, `alphavantage`, `csv_import`, and `felts`
- Updated `docs/mcp/felts-prod-data.md` to describe mart-first MCP access, exact
  schema-qualified relation names, and `scripts/update-prod-data-access.sh` as the
  rerunnable production access reconciliation step.
- Verification on 2026-07-25:
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q` -> `30 passed in 0.22s`

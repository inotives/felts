---
id: task-0001
title: "Phase 09: schema-qualified MCP allowlist"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-13
updated_on: 2026-07-13
priority: normal
parent: ""
depends_on: []
---

# Task

## Context
Phase 09 production-data MCP is implemented, but the handoff at
`docs/2026-06-26-1427_phase-09-prod-data-mcp_handoff.md` records a remaining
blocker: the MCP assumes allowlisted views are in `public`, while production dbt
objects also live under `coingecko` and `csv_import`.

Source of truth:
- `docs/phases/phase_09_production_data_agent_access.md`
- `docs/adr/0005-felts-owned-production-data-mcp.md`
- `docs/mcp/felts-prod-data.md`

## Goal
Make the MCP policy schema-qualified end to end: committed allowlist entries,
query validation, `list_views`, and `describe_view`.


## Scope
- Change `settings/felts-prod-data-views.txt` to exact `schema.view` entries.
- Keep `settings/felts-prod-data-views.txt` as the single MCP allowlist source.
- Update `src/felts/prod_data_mcp.py` so `validate_query` accepts only exact
  schema-qualified references from the allowlist.
- Reject bare view names, including names that would otherwise be unambiguous.
- Update `describe_allowed_view` to split `schema.view` and query
  `information_schema.columns` by both schema and table.
- Keep raw schemas, raw provider tables, mutations, comments, semicolons,
  non-aggregate no-`LIMIT` queries, and non-allowlisted functions rejected.
- Do not add a compatibility layer for bare relation names.


## Planner Notes
This is the root fix from the Phase 09 handoff. Keep it small: prefer parsing
`schema.view` once and reusing exact string matching over inventing a relation
object model.


## Implementation Plan
1. Update the committed allowlist to the schema-qualified entries from the Phase
   09 doc.
2. Update `load_allowed_views` or nearby helper code only as needed to preserve
   exact qualified names.
3. Update SQL table validation to compare `schema.table` against the allowlist.
4. Update `describe_allowed_view` to require an allowlisted qualified name and
   query column metadata using the split schema and table.
5. Update focused unit tests in `tests/unit/test_prod_data_mcp.py`.


## Acceptance Criteria

- [ ] `load_allowed_views()` returns exact schema-qualified allowlist entries.
- [ ] `validate_query` accepts an exact qualified query such as
  `select coin_id from coingecko.mart_coingecko__coins limit 10`.
- [ ] `validate_query` accepts an exact qualified aggregate query such as
  `select count(*) from public.stg_alphavantage__time_series_daily`.
- [ ] `validate_query` rejects bare references such as
  `select * from mart_coingecko__coins limit 10`.
- [ ] `validate_query` still rejects raw-table access, mutations, missing
  `LIMIT`, comments, semicolons, and non-allowlisted functions.
- [ ] `describe_allowed_view("coingecko.mart_coingecko__coins", ...)` looks up
  columns using `table_schema = 'coingecko'` and
  `table_name = 'mart_coingecko__coins'`.
- [ ] `list_views` still returns only committed allowlist entries.
- [ ] Focused tests in `tests/unit/test_prod_data_mcp.py` pass.

## Notes

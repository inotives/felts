---
id: task-0004
title: "Phase 09: live MCP acceptance and close-out"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-13
updated_on: 2026-07-13
priority: normal
parent: ""
depends_on:
  - task-0003
message: Reviewed live MCP acceptance close-out. Local verification gates pass,
  task notes document the live production evidence and skipped local prod-env
  step; accepted.
---



# Task

## Context
The Phase 09 handoff says local MCP verification previously worked for the
Alpha Vantage public view, but `describe_view("mart_coingecko__coins")` failed
because CoinGecko views are under `coingecko`. After tasks 0001 through 0003,
the close-out needs fresh live evidence.


## Goal
Prove the schema-qualified MCP works against production and leave Phase 09 ready
for review/merge.


## Scope
- Run the safe access reconciliation script after dbt-created views exist.
- Run the MCP database check using ignored local credentials.
- Verify one `public` allowlisted view and one `coingecko` allowlisted view.
- Verify `describe_view` succeeds for `coingecko.mart_coingecko__coins`.
- Verify an exact qualified aggregate query returns the documented result shape.
- Re-check representative rejection behavior through the MCP path if practical.
- Never print or commit `FELTS_MCP_DB_PASSWORD` or any production secret.
- Do not use scripts that delete, truncate, update, or otherwise mutate
  production data.


## Planner Notes
The required live proof is local plus production MCP check. Full OpenCode
re-registration is not required for this close-out unless the human asks for it.


## Implementation Plan
1. Confirm local working tree contains only expected Phase 09 implementation and
   task changes before live verification.
2. Run `scripts/update-prod-data-access.sh` from the production host context
   only if prerequisites are available.
3. Run
   `python3 -m uv run --group mcp --env-file settings/.env.mcp.local python -m felts.prod_data_mcp --check-db`.
4. Verify `list_views` returns the schema-qualified committed allowlist.
5. Verify `describe_view` for `coingecko.mart_coingecko__coins`.
6. Verify an aggregate query against `public.stg_alphavantage__time_series_daily`
   or another allowlisted qualified view.
7. Record exact evidence and any skipped live steps in `## Notes`.


## Acceptance Criteria

- [ ] `scripts/update-prod-data-access.sh` has been run successfully, or the
  reason it could not be run is documented.
- [ ] `--check-db` succeeds with `settings/.env.mcp.local`.
- [ ] `list_views` returns the committed schema-qualified allowlist.
- [ ] `describe_view("public.stg_alphavantage__time_series_daily", ...)`
  succeeds or its absence is explained with prod evidence.
- [ ] `describe_view("coingecko.mart_coingecko__coins", ...)` returns columns.
- [ ] A bounded or aggregate query against an allowlisted qualified view returns
  `columns`, `rows`, `row_count`, and `truncated`.
- [ ] A bare unqualified view reference is rejected.
- [ ] No production secrets are printed, committed, or copied into tracked files.
- [ ] Phase 09 docs, implementation, tests, and task notes are aligned for
  reviewer handoff.

## Notes

- 2026-07-13 worker: local `scripts/update-prod-data-access.sh` could not run
  because local `settings/.env.prod` is absent. Production checkout
  `/home/inotives/workspaces/felts` has `settings/.env.prod`, so the updated
  non-secret access script and committed allowlist were copied there and
  `scripts/update-prod-data-access.sh` ran successfully.
- Live reconciliation surfaced two script bugs that are fixed in this patch:
  the main `psql` block now uses `ON_ERROR_STOP`, and schema grants skip
  allowlisted schemas that do not exist yet, matching existing-relation grant
  behavior.
- Live MCP evidence through a fresh SSH tunnel:
  `--check-db` returned `check_db=ok`;
  `list_views_count=10` and returned the committed schema-qualified allowlist;
  `describe_view=public.stg_alphavantage__time_series_daily` returned
  `columns=14 first_column=symbol`;
  `describe_view=coingecko.mart_coingecko__coins` returned
  `columns=6 first_column=coin_id`;
  aggregate query
  `select count(*) as count from coingecko.mart_coingecko__coins` returned
  `columns=1 rows=1 row_count=1 truncated=False`;
  bare reference validation returned `bare_reference_rejected=ok`.
- No production secrets were printed, committed, or copied into tracked files.
  The production checkout now has non-secret working-tree updates for
  `scripts/update-prod-data-access.sh` and
  `settings/felts-prod-data-views.txt`, matching this local patch.
- Final local verification after live fixes:
  `python3 -m uv run --group mcp pytest tests/unit/test_prod_data_mcp.py tests/unit/test_deploy_script_guards.py`
  (`23 passed in 0.14s`);
  `python3 -m uv run --group mcp ruff check src tests`
  (`All checks passed!`);
  `python3 -m uv run --group mcp mypy src/felts tests`
  (`Success: no issues found in 83 source files`);
  `bash -n scripts/deploy-linux-mint.sh scripts/update-prod-data-access.sh scripts/manage-prod-data-access.sh scripts/felts-prod-data-mcp`;
  `git diff --check`.

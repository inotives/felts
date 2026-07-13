---
id: task-0002
title: "Phase 09: schema-aware production access grants"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-13
updated_on: 2026-07-13
priority: normal
parent: ""
depends_on:
  - task-0001
---

# Task

## Context
Task 0001 makes the MCP schema-qualified. The production access reconciliation
script must follow the same allowlist without keeping a second hard-coded copy.

Source of truth:
- `settings/felts-prod-data-views.txt`
- `docs/phases/phase_09_production_data_agent_access.md`
- `docs/mcp/felts-prod-data.md`

## Goal
Make `scripts/update-prod-data-access.sh` read the committed allowlist and grant
the minimum schema/view privileges needed for the schema-qualified MCP policy.


## Scope
- Remove the script's inline view list.
- Read non-empty, non-comment entries from `settings/felts-prod-data-views.txt`.
- Grant `USAGE` on each distinct allowlisted schema.
- Grant `SELECT` on each exact allowlisted relation if that relation exists.
- Preserve password creation/rotation behavior already owned by the script.
- Preserve the production golden rule: no `DROP`, `TRUNCATE`, `DELETE`, or
  data-changing `UPDATE`.
- Keep `scripts/deploy-linux-mint.sh` as bootstrap-only; do not move access
  reconciliation back into deploy.


## Planner Notes
Use the allowlist file as the single source of truth. Shell is acceptable here,
but keep parsing boring: split on the first dot and fail clearly if an allowlist
entry is not `schema.view`.


## Implementation Plan
1. Read allowlist entries from `settings/felts-prod-data-views.txt` in
   `scripts/update-prod-data-access.sh`.
2. Fail clearly on malformed entries without running partial grants.
3. Pass the allowlist into the existing `psql` block in a simple, reviewable
   form.
4. Grant `USAGE` per schema and `SELECT` per relation using quoted identifiers.
5. Update `tests/unit/test_deploy_script_guards.py` for single-source allowlist
   behavior and non-destructive script guarantees.


## Acceptance Criteria

- [ ] `scripts/update-prod-data-access.sh` no longer contains its own inline
  list of allowlisted views.
- [ ] The script reads from `settings/felts-prod-data-views.txt`.
- [ ] The script grants `USAGE` on each distinct schema from the allowlist.
- [ ] The script grants `SELECT` on each existing allowlisted relation using
  schema and relation identifiers.
- [ ] Malformed allowlist entries fail clearly before applying partial grants.
- [ ] The script still supports `--rotate-ai-password`.
- [ ] Tests assert the access script does not contain `DROP`, `TRUNCATE`,
  `DELETE`, or data-changing `UPDATE`.
- [ ] Focused tests in `tests/unit/test_deploy_script_guards.py` pass.

## Notes

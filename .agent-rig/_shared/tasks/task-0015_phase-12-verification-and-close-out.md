---
id: task-0015
title: "Phase 12: verification and close-out"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-25
priority: normal
parent: ""
depends_on:
  - task-0014
---



# Task

## Context

Tasks 0013 and 0014 implement the Phase 12 mart-first MCP access refresh. This task
proves the change and updates implemented-state docs.

Source of truth:

- `docs/phases/phase_12_analytical_access_refresh.md`

## Goal

Run final local verification for Phase 12 and update implemented-state docs without
running production reconciliation.

## Scope

- Run fast checks:
  - `./.venv/bin/ruff check .`
  - `./.venv/bin/ruff format --check .`
  - `./.venv/bin/python -m mypy`
  - `./.venv/bin/pytest tests/unit`
- Run focused MCP tests:
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py`
- Run script syntax check:
  - `bash -n scripts/update-prod-data-access.sh`
- Update implemented-state docs after checks pass.
- Record exact command evidence in `## Notes`.
- Do not run `scripts/update-prod-data-access.sh` against production.
- Do not archive the Phase 12 doc unless the human explicitly asks after merge.

## Planner Notes

Local proof is enough for this phase. Production access reconciliation is an operator
step after deployment and dbt have created the relations in production.

## Implementation Plan

1. Confirm task dependencies are done or ready for review.
2. Run focused MCP tests.
3. Run the full fast local checks.
4. Run the shell syntax check for the access reconciliation script.
5. Update docs that describe the implemented MCP allowlist/access surface.
6. Record exact commands and outcomes in this task's notes.

## Acceptance Criteria

- [ ] Focused MCP tests pass.
- [ ] Fast local checks pass.
- [ ] `bash -n scripts/update-prod-data-access.sh` passes.
- [ ] Implemented-state docs describe mart-first MCP access.
- [ ] Task notes contain exact verification commands and results.
- [ ] No production reconciliation command is run.

## Notes


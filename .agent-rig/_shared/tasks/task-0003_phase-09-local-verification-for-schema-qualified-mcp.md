---
id: task-0003
title: "Phase 09: local verification for schema-qualified MCP"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-13
updated_on: 2026-07-13
priority: normal
parent: ""
depends_on:
  - task-0002
---

# Task

## Context
Tasks 0001 and 0002 should leave the implementation and access script aligned
with the updated Phase 09 docs. This task is the local verification gate before
any production check.


## Goal
Run the focused local verification suite and fix any Phase 09 regressions found
by those checks.


## Scope
- Run the Phase 09 unit tests for MCP behavior and deploy/access script guards.
- Run static checks for the touched Python code.
- Run shell syntax checks for the production scripts.
- Fix only failures caused by the schema-qualified allowlist work.
- Do not perform production SSH, Docker, or live MCP verification in this task.


## Planner Notes
Keep this as a verification task, not a refactor task. If unrelated failures
appear, record them in `## Notes` and do not broaden the patch unless the human
approves.


## Implementation Plan
1. Run the focused pytest command.
2. Run ruff and mypy for the Felts source/tests scope.
3. Run bash syntax checks for the relevant scripts.
4. Fix task-related failures only.
5. Record exact commands and results in `## Notes`.


## Acceptance Criteria

- [ ] `python3 -m uv run --group mcp pytest tests/unit/test_prod_data_mcp.py tests/unit/test_deploy_script_guards.py` passes.
- [ ] `python3 -m uv run --group mcp ruff check src tests` passes.
- [ ] `python3 -m uv run --group mcp mypy src/felts tests` passes.
- [ ] `bash -n scripts/deploy-linux-mint.sh scripts/update-prod-data-access.sh scripts/manage-prod-data-access.sh scripts/felts-prod-data-mcp` passes.
- [ ] `git diff --check` passes.
- [ ] Any unrelated failure is documented in `## Notes` with evidence and left
  out of scope.

## Notes

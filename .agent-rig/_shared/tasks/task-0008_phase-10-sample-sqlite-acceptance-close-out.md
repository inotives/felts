---
id: task-0008
title: "Phase 10: sample SQLite acceptance close-out"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-14
updated_on: 2026-07-14
priority: normal
parent: ""
depends_on:
  - task-0007
---

# Task

## Context

Tasks 0005 through 0007 implement the Phase 10 agent-pipe import path. This task
proves the feature with the real local sample database and leaves the branch ready for
review.

Source of truth:

- `docs/phases/phase_10_agent_pipe_sqlite_ingestion.md`

Sample evidence database:

- `/Users/inotives/workspaces/agent-pipe/.agent-pipe/data/local.sqlite`

## Goal

Run the final checks and record acceptance evidence for Phase 10.

## Scope

- Run the focused unit tests for the agent-pipe source.
- Run the standard Python checks for the changed code.
- Run the import against the sample agent-pipe SQLite database if local Postgres
  prerequisites are available.
- If Postgres prerequisites are unavailable, run the closest non-mutating SQLite
  extraction proof and document the skipped raw-load step.
- Verify the sample database includes multiple entities.
- Verify project id `agent-pipe` maps to raw source/schema `agent_pipe`.
- Record exact commands and results in `## Notes`.
- Do not print or commit local secrets.
- Do not mutate the sample agent-pipe SQLite database.

## Planner Notes

The sample path is local proof only. Do not turn it into a setting default or fixture
path in committed code.

## Implementation Plan

1. Confirm working-tree changes are scoped to Phase 10.
2. Run focused unit tests.
3. Run `ruff` and `mypy` for changed source/tests.
4. Inspect the sample database counts by project/entity.
5. Run the import path against the sample database if safe local database credentials
   are available.
6. Record exact acceptance evidence and any skipped prerequisites in task notes.

## Acceptance Criteria

- [ ] Focused Phase 10 tests pass.
- [ ] Ruff passes for changed files.
- [ ] Mypy passes for changed files or the full configured source set.
- [ ] The sample SQLite database is inspected without mutation.
- [ ] Live/sample evidence shows multiple entities are readable.
- [ ] Evidence confirms `project_id` `agent-pipe` maps to `agent_pipe`.
- [ ] Raw-load acceptance is run, or the missing local prerequisite is documented.
- [ ] No local sample path is hardcoded into source defaults.
- [ ] No secrets are printed or committed.
- [ ] Task notes contain exact commands and results for reviewer handoff.

## Notes

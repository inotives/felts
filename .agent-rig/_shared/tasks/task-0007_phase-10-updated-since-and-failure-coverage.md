---
id: task-0007
title: "Phase 10: updated-since and failure coverage"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-14
updated_on: 2026-07-14
priority: normal
parent: ""
depends_on:
  - task-0006
message: Reviewed updated-since filtering and malformed JSON coverage. Focused
  pytest, ruff, and mypy checks passed; accepted.
---



# Task

## Context

Phase 10 accepts either full reruns or a caller-provided incremental filter. This task
adds the optional filter and tightens failure behavior after the base import path
exists.

Source of truth:

- `docs/phases/phase_10_agent_pipe_sqlite_ingestion.md`

## Goal

Add `--updated-since <iso-timestamp>` support and clear failure behavior for malformed
agent-pipe JSON data.

## Scope

- Add optional `--updated-since` to the CLI, runner, and extractor as needed.
- Filter on `records.updated_at`.
- Omitted `--updated-since` still imports all rows.
- Parse ISO timestamps consistently with existing project style.
- Malformed `payload_json` fails clearly.
- Malformed non-empty `metadata_json` fails clearly.
- Empty or null `metadata_json` becomes an empty metadata object.
- Keep importing soft-deleted rows when they match the filter.
- Do not add stored cursors or persistent sync state.

## Planner Notes

This is intentionally caller-managed incremental sync. Avoid inventing state tables or
checkpoint files.

## Implementation Plan

1. Thread `updated_since` through the CLI, runner, and SQLite query.
2. Add filtering against `records.updated_at`.
3. Add direct tests for included and excluded rows.
4. Add malformed JSON tests.
5. Re-run focused source tests.

## Acceptance Criteria

- [x] `felts agent-pipe import --sqlite-path <path> --updated-since <timestamp>` is
  accepted.
- [x] Rows with `updated_at` after the filter are imported.
- [x] Rows before the filter are skipped.
- [x] Omitted `--updated-since` imports all rows.
- [x] Soft-deleted rows are still imported when they match the filter.
- [x] Malformed `payload_json` fails clearly.
- [x] Malformed non-empty `metadata_json` fails clearly.
- [x] No stored cursor or scheduler state is added.
- [x] Focused tests pass.

## Notes

- Threaded optional `updated_since` through
  `AgentPipeSQLiteExtractor`, `run_agent_pipe_import(...)`, and
  `felts agent-pipe import --updated-since`.
- Filter uses parsed ISO timestamps from `records.updated_at`, preserving
  soft-deleted rows that match the caller-provided cutoff.
- Added malformed non-empty `metadata_json` coverage; empty/null metadata still
  becomes `{}`.
- Verification:
  - `python3 -m uv run --group dev pytest tests/unit/sources/agent_pipe -q`
    -> `8 passed`
  - `python3 -m uv run --group dev ruff check src/felts/sources/agent_pipe tests/unit/sources/agent_pipe`
    -> `All checks passed!`
  - `python3 -m uv run --group dev mypy src/felts/sources/agent_pipe tests/unit/sources/agent_pipe`
    -> `Success: no issues found in 8 source files`

---
id: task-0006
title: "Phase 10: raw writer runner and CLI import"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-14
updated_on: 2026-07-14
priority: normal
parent: ""
depends_on:
  - task-0005
message: Reviewed raw writer runner and CLI import. Focused pytest, ruff, and
  mypy checks passed; accepted.
---



# Task

## Context

Task 0005 adds the agent-pipe SQLite extraction contract. This task wires that
contract into the normal Felts raw writer and CLI path.

Source of truth:

- `docs/phases/phase_10_agent_pipe_sqlite_ingestion.md`

Existing source runners and CLIs to follow:

- `src/felts/sources/csv_import/runner.py`
- `src/felts/sources/csv_import/cli.py`
- `src/felts/cli.py`

## Goal

Add `felts agent-pipe import --sqlite-path <path>` so agent-pipe records can land
through the existing `RawWriter` and Postgres raw loader.

## Scope

- Add a runner that writes extracted agent-pipe records through `RawWriter`.
- Use `create_loader(settings)` and `settings.loader_batch_size`.
- Register the CLI under top-level `felts`.
- Require `--sqlite-path`.
- Print a source/entity summary consistent with existing source CLIs.
- Keep `--updated-since` out of this task; task 0007 adds it.
- Do not add dbt models.
- Do not add scheduler or stored cursor behavior.
- Do not hardcode the local sample database path.

## Planner Notes

Keep the runner shaped like existing Felts source runners. The existing loader already
derives raw schema from `ExtractedRecord.source`, so no core loader change should be
needed.

## Implementation Plan

1. Add `run_agent_pipe_import(...)` that accepts a SQLite path, optional settings, and
   optional writer for tests.
2. Build a `RawWriter` using the existing loader factory when no writer is provided.
3. Write records emitted by the task 0005 extractor.
4. Return a `SourceRunSummary` grouped by emitted entities.
5. Add CLI registration and top-level import/call wiring.
6. Add focused unit tests for runner and CLI behavior.

## Acceptance Criteria

- [x] `felts agent-pipe import --sqlite-path <path>` is registered.
- [x] Missing `--sqlite-path` fails through argparse.
- [x] The runner uses the existing `RawWriter` path.
- [x] The runner returns a `SourceRunSummary`.
- [x] Multiple agent-pipe entities produce separate entity summaries.
- [x] For project id `agent-pipe`, records are written with source `agent_pipe`,
  allowing the existing loader to target `agent_pipe.raw_<entity>`.
- [x] No loader schema override is introduced.
- [x] Focused runner and CLI tests pass.

## Notes

- Added `run_agent_pipe_import(...)` in
  `src/felts/sources/agent_pipe/runner.py`, using `RawWriter`,
  `create_loader(settings)`, and `settings.loader_batch_size`.
- Added `felts agent-pipe import --sqlite-path <path>` CLI wiring through
  `src/felts/sources/agent_pipe/cli.py` and `src/felts/cli.py`.
- Added focused runner and CLI tests under `tests/unit/sources/agent_pipe/`.
- Verification:
  - `python3 -m uv run --group dev pytest tests/unit/sources/agent_pipe -q`
    -> `5 passed`
  - `python3 -m uv run --group dev ruff check src/felts/cli.py src/felts/sources/agent_pipe tests/unit/sources/agent_pipe`
    -> `All checks passed!`
  - `python3 -m uv run --group dev mypy src/felts/cli.py src/felts/sources/agent_pipe tests/unit/sources/agent_pipe`
    -> `Success: no issues found in 9 source files`

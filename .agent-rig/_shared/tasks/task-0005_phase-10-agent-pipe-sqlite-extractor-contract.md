---
id: task-0005
title: "Phase 10: agent-pipe SQLite extractor contract"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-14
updated_on: 2026-07-14
priority: normal
parent: ""
depends_on: []
---

# Task

## Context

Phase 10 adds Felts ingestion for records from an `agent-pipe` project-local SQLite
database. The phase doc is the source of truth:

- `docs/phases/phase_10_agent_pipe_sqlite_ingestion.md`

The sample database for live acceptance is:

- `/Users/inotives/workspaces/agent-pipe/.agent-pipe/data/local.sqlite`

That sample path is evidence only. Do not hardcode it as a default.

## Goal

Add the minimal source-side extraction contract that reads agent-pipe `records` rows
and emits Felts `ExtractedRecord` objects.

## Scope

- Add an `agent_pipe` source package under `src/felts/sources/`.
- Use Python standard-library `sqlite3`; do not add a dependency.
- Read only the `records` table.
- Do not read or ingest `job_runs` or `schema_migrations`.
- Normalize `records.project_id` into a Felts-safe source identifier.
- Preserve `records.entity` as the Felts entity.
- Set `ExtractedRecord.source_record_id` to `records.id`.
- Include active and soft-deleted rows.
- Build the envelope payload described in the Phase 10 doc.
- Parse `payload_json` into the envelope `payload`.
- Parse `metadata_json` into `agent_pipe.metadata`.
- Keep this task focused on extraction; CLI and raw loading are in later tasks.

## Planner Notes

The lazy path is to make this a plain SQLite row-to-`ExtractedRecord` adapter. Do
not introduce a loader schema override, replication abstraction, or dbt layer.

## Implementation Plan

1. Add source constants for the feature only if they reduce repetition.
2. Add a small extractor/helper that opens a provided SQLite path and selects rows
   from `records`.
3. Convert each row to an `ExtractedRecord`.
4. Add source normalization for agent-pipe `project_id` values such as `agent-pipe`
   to `agent_pipe`.
5. Add focused unit tests with a temporary SQLite database.

## Acceptance Criteria

- [ ] A temporary SQLite database with the agent-pipe `records` schema can be read.
- [ ] `project_id` `agent-pipe` maps to `ExtractedRecord.source == "agent_pipe"`.
- [ ] `records.entity` is preserved as `ExtractedRecord.entity`.
- [ ] `records.id` is used as `ExtractedRecord.source_record_id`.
- [ ] The envelope contains agent-pipe row metadata and parsed payload JSON.
- [ ] Rows with non-null `deleted_at` are emitted, not filtered.
- [ ] No code reads `job_runs` or `schema_migrations`.
- [ ] Focused unit tests for the extractor pass.

## Notes

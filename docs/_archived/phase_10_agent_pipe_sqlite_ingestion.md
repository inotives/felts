# Phase 10 - Agent-Pipe SQLite Raw Ingestion

## Goal

Allow Felts to ingest records from an `agent-pipe` project-local SQLite database
under `.agent-pipe/data/` and land them as Felts raw records.

This phase treats `agent-pipe` as a local project datastore. Felts reads its stable
`records` table, preserves the original agent-pipe project and entity identity, and
uses the existing Felts raw writer and PostgreSQL raw loader path.

## Context

- `agent-pipe` can be initialized in any project repository under that project's
  `.agent-pipe/` folder.
- Each agent-pipe project has a `projectId` in `.agent-pipe/project.yaml`.
- Each configured SQLite database lives under `.agent-pipe/data/`.
- The sample implementation database for planning and live acceptance is:
  `/Users/inotives/workspaces/agent-pipe/.agent-pipe/data/local.sqlite`.
- That sample path is local evidence only; it is not a committed default or portable
  contract.
- The stable agent-pipe datastore table for this phase is `records`.
- Phase 10 does not mirror agent-pipe; it imports records as Felts raw evidence.

## Agent-Pipe Input Contract

Phase 10 reads only the agent-pipe `records` table:

```sql
records (
  id text primary key,
  project_id text not null,
  entity text not null,
  local_id text not null,
  source text,
  captured_at text,
  payload_json text not null,
  metadata_json text,
  created_at text not null,
  updated_at text not null,
  deleted_at text
)
```

The agent-pipe `job_runs` and `schema_migrations` tables are not ingested in this
phase.

## Decisions

- Add a Felts source adapter for agent-pipe SQLite databases.
- Use Python standard-library `sqlite3`; do not add a new dependency.
- Add a CLI entrypoint:

```bash
felts agent-pipe import --sqlite-path <path> [--updated-since <iso-timestamp>]
```

- `--sqlite-path` is required.
- `--updated-since` is optional.
- When `--updated-since` is omitted, Felts imports all rows and relies on raw-load
  idempotency to skip duplicates.
- When `--updated-since` is provided, Felts filters on `records.updated_at`.
- The Felts raw schema name is derived from the agent-pipe `project_id`, not from the
  literal adapter name `agent_pipe`.
- `project_id` is normalized into a Felts-safe source identifier before it is assigned
  to `ExtractedRecord.source`.
- Example: agent-pipe `project_id` `agent-pipe` lands as `agent_pipe.raw_<entity>`.
- The agent-pipe `records.entity` value is preserved as the Felts entity.
- `ExtractedRecord.source_record_id` is the agent-pipe `records.id`.
- Active and soft-deleted rows are both imported.
- Soft delete state is preserved through `deleted_at`; extraction does not filter it.
- The raw payload is an envelope:

```json
{
  "agent_pipe": {
    "id": "...",
    "project_id": "...",
    "local_id": "...",
    "source": "...",
    "captured_at": "...",
    "metadata": {},
    "created_at": "...",
    "updated_at": "...",
    "deleted_at": null
  },
  "payload": {}
}
```

- The parsed `payload_json` value becomes the envelope `payload`.
- The parsed `metadata_json` value becomes `agent_pipe.metadata`.
- Malformed `payload_json` or `metadata_json` fails clearly rather than landing
  ambiguous data.
- `projectName` is descriptive only and is not used for schema names.
- Phase 10 stops at raw landing.

## Acceptance Criteria

- Phase 10 planning docs are committed to `main` before the implementation branch is
  created.
- The implementation adds an agent-pipe source adapter, CLI entrypoint, runner, and
  focused tests.
- The implementation imports rows from an agent-pipe SQLite `records` table into the
  existing Felts raw writer path.
- A project with agent-pipe `project_id` `agent-pipe` lands rows into
  `agent_pipe.raw_<entity>`.
- Multiple entities from the same SQLite database land into separate raw entity tables.
- Soft-deleted rows are preserved.
- `--updated-since` filters rows by `records.updated_at`.
- Re-running without `--updated-since` is safe and idempotent through the existing raw
  loader behavior.
- Unit tests cover:
  - SQLite extraction from a temporary agent-pipe-style database;
  - project id normalization;
  - entity preservation;
  - envelope payload construction;
  - soft-deleted row preservation;
  - `--updated-since` filtering;
  - malformed JSON failure;
  - required CLI `--sqlite-path` handling.
- Live acceptance uses
  `/Users/inotives/workspaces/agent-pipe/.agent-pipe/data/local.sqlite` as sample
  evidence and records the command/result in the task notes or PR.

## Out of Scope Until Explicitly Approved

- Ingesting `job_runs`.
- Ingesting `schema_migrations`.
- Stored incremental cursors.
- A scheduler for recurring agent-pipe ingestion.
- dbt staging, intermediate, or mart models for agent-pipe records.
- Dynamic loader schema overrides.
- Using `projectName` for schema names.
- Hardcoding local sample paths into Felts settings or code.

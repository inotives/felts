# Phase 01 - Core Contracts and Local Foundation

## Goal

Establish the shared Felts contracts that every later source, loader, flow, and transform relies on.

## Core Functionality

- Typed settings via `pydantic-settings`.
- Universal raw record contract.
- Schema registry for `source + entity -> Pydantic model`.
- Base extractor and loader interfaces.
- Local Postgres as the first runnable warehouse target.

## Scope

- Create `pipeline/core/extractors/base_extractor.py`.
- Create `pipeline/core/loaders/base_loader.py`.
- Create `pipeline/core/loaders/postgres_loader.py`.
- Create `pipeline/core/loaders/factory.py`.
- Create `pipeline/core/loaders/writer.py`.
- Create `pipeline/core/schemas/raw_record.py`.
- Create `pipeline/core/schemas/registry.py`.
- Create `pipeline/config/settings.py`.
- Add local Postgres configuration needed to exercise the first loader.

## Acceptance Criteria

- A test can create a valid `RawRecord`.
- A test can register and retrieve a Pydantic schema by `source` and `entity`.
- A test can instantiate the loader factory for `postgres`.
- A local Postgres table can receive a raw JSON payload through the writer path.
- Core modules contain no source-specific logic.
- Phase 00 project scaffolding remains unchanged except for adding required dependencies or configuration.

## Out of Scope

- BigQuery, Snowflake, and ClickHouse implementations.
- Prefect deployments and automations.
- dbt transformations.
- Streaming extraction.
- Multi-target fan-out.

## Grill Questions

- Is Postgres definitely the first target, or should the first target be DuckDB for local development speed?
- Should raw table creation live in the loader, migrations, or dbt/source bootstrap scripts?
- Should the raw record ID be random UUID, deterministic hash, or loader-specific?
- Should invalid records be loaded with `is_valid = false`, or rejected before landing?

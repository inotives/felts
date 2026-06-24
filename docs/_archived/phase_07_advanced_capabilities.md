# Phase 07 - Advanced and Deferred Capabilities

## Outcome

No listed capability currently has a concrete business or operational driver.
Implementation is deferred, and the capabilities remain tracked under
`Future Implementation` in `docs/project_specs.md`.

## Goal

Track powerful but non-MVP capabilities so they are not accidentally designed into the early system before requirements justify them.

## Core Functionality

- Streaming and real-time ingestion.
- Multi-target fan-out.
- Additional warehouse targets.
- Automated schema versioning and migration.
- Advanced CSV import user experience.

## Scope

- Design `src/felts/core/extractors/stream.py` only after latency requirements are known.
- Decide whether WebSocket and Kafka should remain inside Prefect micro-batches or move to a stream processor.
- Add BigQuery, Snowflake, and ClickHouse loaders after Postgres is proven.
- Add fan-out writer behavior only if simultaneous multi-target writes are required.
- Add schema drift detection and schema-version transition handling.
- Add web UI, SFTP, or object-store event triggers for CSV import only after the ingestion workflow is clear.

## Acceptance Criteria

- Each advanced capability has a concrete business or operational driver before implementation.
- Multi-target writes define partial-failure behavior before coding starts.
- Streaming sources define acceptable latency and transformation cadence before coding starts.
- Schema evolution defines how staging models read old and new versions.

## Out of Scope

- Anything required for the first working ELT path.
- Speculative abstractions for unchosen warehouses.
- Stream processor infrastructure before true streaming is required.

## Grill Questions

- What source actually requires seconds-level latency?
- If streaming is only minute-level, can Prefect micro-batches cover it?
- Do we need simultaneous warehouse fan-out, or just environment-specific targets?
- What is the first real schema evolution case we expect from financial APIs?

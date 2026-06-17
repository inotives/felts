# Phase 06 - Operational Hardening

## Goal

Make Felts reliable enough for repeated use outside local development.

## Core Functionality

- Backfill pattern.
- Observability and alerting.
- Secret management.
- Testing strategy.
- Data quality checks.
- CI workflow.

## Scope

- Add explicit backfill flow deployments with date range parameters.
- Keep backfill data in normal raw tables unless grilling identifies a strong reason for `backfill_raw`.
- Add source-level and dbt-level failure notifications.
- Decide `.env`, Prefect Blocks, or external secrets manager for each environment.
- Add integration tests with local Postgres.
- Add dbt tests to CI.
- Add basic monitoring tables only if required by an operational use case.

## Acceptance Criteria

- A backfill can re-ingest a bounded date range without corrupting staging outputs.
- Staging dedup handles overlap between live loads and backfills.
- CI runs unit tests, integration tests, and dbt tests at the agreed scope.
- Failures produce actionable alerts.
- Secret handling does not require code changes for rotation in deployed environments.

## Out of Scope

- Full data observability platform.
- PagerDuty-style incident management unless required.
- Automated schema migration framework.
- Multi-region or high-availability deployment.

## Grill Questions

- Should backfills be separate deployments or parameterized re-runs of source flows?
- Is a separate `backfill_raw` schema worth the extra complexity?
- Which failures are urgent alerts versus normal run failures?
- Should schema drift detection block loads, warn and load invalid rows, or quarantine records?


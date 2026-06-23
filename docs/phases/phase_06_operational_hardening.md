# Phase 06 - Operational Hardening

## Goal

Make Felts reliable enough for repeated use outside local development.

The intended operational pipeline is: ingest data from a Source such as an API
or CSV file, persist RawRecords into raw tables, run dbt models into staging,
intermediate, and mart models, then consume those models through visualization
or query tools such as Grafana.

## Core Functionality

- Backfill pattern.
- Observability and alerting.
- Secret management.
- Testing strategy.
- Data quality checks.
- CI workflow.

## Scope

- Harden for single-machine/local-docker operation plus GitHub Actions CI in Phase 06.
- Implement Phase 06 in one implementation PR.
- Add explicit backfill flow deployments with `start_date` and `end_date` parameters.
- Define backfill as a bounded replay Source Run that lands into normal raw tables.
- Apply Phase 06 backfill only to CSV import. Do not add CoinGecko backfill until a real historical endpoint exists.
- Keep backfill data in normal raw tables; do not add `backfill_raw` in Phase 06.
- Treat Prefect failed states and GitHub Actions failed checks as the Phase 06 actionable alerts.
- Ensure source flow, dbt run, and dbt test failures surface useful failure messages.
- Decide `.env`, Prefect Blocks, or external secrets manager for each environment.
- Add integration tests with local Postgres.
- Keep Phase 06 CI to the fast job: Ruff lint, Ruff format check, mypy, and unit tests.
- Defer DB-backed CI, integration-test CI, and dbt-test CI.
- Keep DB-backed integration tests, CSV import smoke checks, and dbt run/test checks as documented local acceptance checks.
- Document how to register the dbt transform deployment, including event triggers and any schedules needed for operational runs.
- Treat dbt model execution as part of the successful pipeline completion path from raw data to queryable models.
- Keep dbt execution event-driven by default: successful raw loads emit Raw Completion Events that trigger the parameterized `dbt-transform` deployment.
- Document manual deployment registration and verification for the raw-to-dbt event chain.
- Limit Phase 06 consumption validation to direct SQL queries over modeled tables.
- Do not add monitoring tables in Phase 06.
- Replace the single `.env` convention with environment-specific files under a repo-level `settings/` directory: `settings/.env.local`, `settings/.env.dev`, and `settings/.env.prod`.
- Map `settings/.env.local` to local Docker operation, `settings/.env.dev` to dev/staging operation, and `settings/.env.prod` to production operation.
- Keep environment files uncommitted and provide committed examples/templates for required keys.
- Load the environment file that corresponds to `FELTS_ENV`.
- Default missing `FELTS_ENV` to `local`, which loads `settings/.env.local`.
- Keep `config.yaml` for safe non-secret project defaults.
- Use `settings/.env.*` for environment-specific runtime values and secrets.
- Record the settings-file decision in `docs/adr/0004-environment-specific-settings-files.md`.
- Do not add an external secrets manager or cloud deployment target in Phase 06.

## Acceptance Criteria

- A backfill can re-ingest a bounded date range without corrupting staging outputs.
- Staging dedup handles overlap between live loads and backfills.
- Backfill overlaps with live loads skip duplicate RawRecords through normal source record identity.
- CSV import has unscheduled backfill deployments with explicit date range parameters.
- CI runs Ruff lint, Ruff format check, mypy, and unit tests.
- Local acceptance checks document the exact commands for DB bootstrap, integration tests, CSV import smoke checks, dbt run/test, and Prefect registration.
- The local operations runbook lives at `docs/runbooks/local_operations.md`.
- Operators can follow documented instructions to deploy or refresh the dbt transform scheduler/triggers when operational runs need them.
- Operational source runs trigger dbt transforms through Raw Completion Events rather than a separate dbt cron schedule.
- Query-ready modeled tables can be inspected directly with SQL after the pipeline completes.
- API source schema drift continues to use the current Pydantic validation boundary, landing invalid RawRecords when validation fails.
- CSV schema drift continues to use strict pre-load header validation according to the YAML contract.
- dbt casting and model-shape failures surface through dbt run/test failures.
- Do not add quarantine tables or automatic schema migrations in Phase 06.
- Use Prefect run history, raw tables, dbt results, and CI checks as the Phase 06 operational evidence.

## Implementation Sequence

1. Update settings loading to use `settings/.env.local` by default and `settings/.env.<FELTS_ENV>` when explicitly selected.
2. Add committed dotenv templates for local, dev/staging, and production keys.
3. Update `.gitignore` for uncommitted `settings/.env.*` files while keeping templates tracked.
4. Update CI to include mypy in the existing fast job.
5. Add CSV-only backfill flow/deployment support with `start_date` and `end_date` parameters.
6. Add tests for environment-file selection and backfill parameter handling.
7. Add `docs/runbooks/local_operations.md` covering environment files, local stack start/stop, DB bootstrap, CSV/API ingestion, Prefect registration, event-triggered dbt verification, manual dbt run/test, direct SQL query checks, and common failure checks.
8. Run fast checks plus documented local acceptance checks before opening the PR.
- Failures produce actionable alerts.
- Phase 06 does not add Slack, email, PagerDuty, or another external notification service.
- Secret handling does not require code changes for rotation in deployed environments.
- Local, dev/staging, and production settings are separated by environment-specific dotenv files.

## Out of Scope

- Full data observability platform.
- PagerDuty-style incident management unless required.
- Slack, email, or webhook notification delivery.
- Automated schema migration framework.
- Multi-region or high-availability deployment.
- DB-backed CI, integration-test CI, and dbt-test CI.
- Cron-scheduled dbt rebuilds unless a concrete operational need appears.
- Grafana, dashboards, and visualization app setup. A later visualization phase can add Grafana as a Dockerized app in this monorepo.
- Monitoring tables for freshness or run summaries.

## Grill Questions

- Should backfills be separate deployments or parameterized re-runs of source flows?
- Is a separate `backfill_raw` schema worth the extra complexity?
- Which failures are urgent alerts versus normal run failures?
- Should schema drift detection block loads, warn and load invalid rows, or quarantine records?

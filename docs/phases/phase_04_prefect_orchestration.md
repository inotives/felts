# Phase 04 - Prefect Flow and Scheduling Foundation

## Goal

Wire the working ELT path into Prefect so extraction, loading, dbt transforms, schedules, and event-triggered chaining work end to end.

## Core Functionality

- Thin source flows for extract-load.
- Entity-scoped raw completion events.
- Transform flow for scoped dbt runs selected by source entity.
- Deployments for scheduled execution.
- Event constants and automation chains.
- A single orchestrator entry point for registration.

## Scope

- Create `src/felts/sources/coingecko/flow.py`.
- Create `src/felts/sources/coingecko/events.py`.
- Create `src/felts/sources/coingecko/deployments.py`.
- Create `src/felts/sources/coingecko/automations.py`.
- Create `src/felts/flows/transform.py`.
- Create `src/felts/flows/master.py`.
- Create shared deployment and automation helpers in `src/felts/schedules/helpers.py` only if needed.
- Create `src/felts/schedules/orchestrator.py`.

## Acceptance Criteria

- A scheduled CoinGecko deployment can run the source flow.
- Each successful CoinGecko entity run emits a raw completion event.
- A raw completion event can trigger a scoped dbt staging or mart flow for the completed entity.
- Flow retries and basic failure handling are configured.
- Adding a new source later requires only a new `src/felts/sources/<source>/` feature folder and one orchestrator registration line.
- No source-specific EL logic is added under shared `src/felts/flows` or `src/felts/schedules` modules.

## Decisions

- Phase 04 orchestration is entity-scoped. A successful raw load for a source entity triggers only the relevant downstream dbt selector chain instead of running every model for the source.
- Phase 04 uses one scheduled source deployment per source entity. Each deployment calls the same source flow with one entity selected.
- Entity-level deployments isolate retries, failures, schedules, and downstream event emission.
- Raw completion events are emitted only when the entity run inserts at least one new raw row. Successful entity runs with only duplicate skips do not trigger dbt.
- Raw completion events use the naming convention `felts.raw.<source>.<entity>.completed`, for example `felts.raw.coingecko.coins_list.completed`.
- Raw completion event payloads include `source`, `entity`, `batch_id`, `inserted_count`, `skipped_count`, `extracted_count`, `failed_count`, and `dbt_selector`.
- Phase 04 does not add custom orchestration state tables. Prefect remains the system of record for flow/deployment state, retries, and logs; Felts stores durable data lineage in raw and transformed models.
- `master_flow.py` is included as a manual run-anytime orchestration entry point. It can run one or more entity pipelines directly for local smoke tests, demos, or manual recovery.
- `master_flow.py` is not the primary production scheduler. Scheduled deployments and raw completion event automations remain the production orchestration path.
- `master_flow.py` defaults to all configured CoinGecko entities, but accepts an entity filter for targeted manual runs.
- For each selected entity, `master_flow.py` runs EL first, then runs the mapped dbt selector only when the entity inserts at least one new raw row.
- A failed entity pipeline should fail the `master_flow.py` run by default.
- Phase 04 dbt execution uses a thin Prefect task that runs shell commands matching the local dbt commands, for example `uv run dbt run --project-dir transforms --profiles-dir transforms --select <selector>`.
- `transform_flow(selector, run_tests=True)` runs the scoped dbt models and, by default, the matching scoped dbt tests.
- Event-triggered transforms run both `dbt run --select <selector>` and `dbt test --select <selector>` by default.
- Phase 04 uses one generic parameterized transform deployment. Source-specific automations pass `selector` and `run_tests` parameters to that deployment instead of creating one transform deployment per entity.
- Source entity to dbt selector mappings live with the source, starting in `src/felts/sources/coingecko/constants.py`.
- Source-local event helpers emit raw completion events, starting with `src/felts/sources/coingecko/events.py`.
- Source-local event helpers enforce the `inserted_count > 0` event gate and build the raw completion event payload.
- CoinGecko exposes both `coingecko_entity_source_flow(entity)` and `coingecko_source_flow(entities=None)`.
- Scheduled entity deployments use `coingecko_entity_source_flow(entity)` so each deployment has one entity, one retry boundary, and one event decision.
- Broader manual runs may use `coingecko_source_flow(entities=None)` or `master_flow.py`.
- Deployment registration uses configurable Prefect work pool and work queue settings, with local defaults such as `FELTS_PREFECT_WORK_POOL=local` and `FELTS_PREFECT_WORK_QUEUE=default`.
- `make prefect-register` ensures the configured local work pool exists before registering deployments and automations.
- `make prefect-register` uses Python registration code in `src/felts/schedules/orchestrator.py` to register deployments and automations.
- Source feature modules expose deployment and automation builders, and the shared orchestrator applies them.
- Prefect Python SDK/API is preferred for automation creation. A small Prefect CLI wrapper is acceptable only if the local Prefect version makes automation SDK usage impractical.
- Registration is idempotent. Re-running `make prefect-register` updates existing deployments and automations instead of creating duplicates.
- Deployment and automation names are stable and deterministic, for example `coingecko-coins-list-source`, `dbt-transform`, and `coingecko-coins-list-raw-completed-to-dbt-transform`.
- Phase 04 live acceptance includes registration verification and one real event-triggered chain.
- The default event-chain live test entity is `global`: run the `global` source deployment manually, insert a new raw row, emit `felts.raw.coingecko.global.completed`, trigger the generic `dbt-transform` deployment, run `stg_coingecko__global+`, and pass scoped dbt tests.
- `master_flow.py` is tested as a manual convenience path, but it does not replace the event-triggered acceptance test.
- Phase 04 keeps `.env` and typed `Settings` as the configuration source. Prefect Blocks for secrets/config are deferred to Phase 06.
- Phase 04 adds settings for Prefect work pool, Prefect work queue, and dbt command defaults as needed.
- Richer `prefect-dbt` block/task integration is deferred until Prefect-specific dbt artifact handling is needed.
- Source entity flows use `retries=2` and `retry_delay_seconds=60`.
- Transform flows use `retries=1` and `retry_delay_seconds=30`.
- dbt shell tasks do not add nested retries beyond the transform flow retry.
- If extraction or loading fails after retries, no raw completion event is emitted.
- If dbt run or dbt test fails after retry, the transform flow fails.
- Initial CoinGecko deployment schedules are daily for `coins_list`, daily for `asset_platforms_list`, hourly for `global`, and hourly for `global_defi`.
- `coins_markets` gets a registered deployment with no schedule in Phase 04. It remains available for manual Prefect runs, `master_flow.py`, and transform mapping, but does not run automatically by default.
- Source-specific orchestration code lives inside the source feature folder, for example `src/felts/sources/coingecko/flow.py`, `events.py`, `deployments.py`, and `automations.py`.
- Source-specific EL ownership stays inside `src/felts/sources/<source>/`. Extractors, runners, schemas, source flows, source deployments, source events, and source automations belong to the source feature folder.
- Shared orchestration code lives under `src/felts/flows` and `src/felts/schedules`, not a separate top-level `pipeline` package.
- Shared `src/felts/flows` modules are limited to cross-source utilities such as dbt transform execution and manual master orchestration. They must not contain CoinGecko-specific extraction or loading behavior.
- Shared `src/felts/schedules` modules are limited to cross-source helpers and orchestrator registration. They must not contain source-specific schedules, deployments, events, or automations.
- CoinGecko raw completion events map to dbt selectors as follows:
  - `coins_list` -> `stg_coingecko__coins_list+`
  - `asset_platforms_list` -> `stg_coingecko__asset_platforms_list+`
  - `coins_markets` -> `stg_coingecko__coins_markets+`
  - `global` -> `stg_coingecko__global+`
  - `global_defi` -> `stg_coingecko__global_defi+`
- The trailing `+` is intentional so dbt runs the staging model and any downstream marts for that entity.
- Descendant selectors also support future shared intermediate models. If an intermediate model joins two staging models, a raw completion event from either upstream entity can rebuild that intermediate model and its downstream marts using the latest available staged data from all dependencies.
- Phase 04 does not require downstream models to consume only records from the same extraction batch.

## Out of Scope

- Advanced alert routing.
- SLA monitoring.
- Streaming orchestration.
- Multi-source event dependency graphs beyond the first source.

## Grill Questions

- Does the local Prefect Python SDK support idempotent automation registration cleanly, or does this phase need the approved CLI fallback?
- What is the smallest reliable way to assert that the `global` event-triggered chain completed locally?
- What is the exact local assertion for confirming the `global` event-triggered transform completed?

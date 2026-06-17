# Phase 04 - Prefect Flow and Scheduling Foundation

## Goal

Wire the working ELT path into Prefect so extraction, loading, dbt transforms, schedules, and event-triggered chaining work end to end.

## Core Functionality

- Thin source flows for extract-load.
- Transform flow for scoped dbt runs.
- Deployments for scheduled execution.
- Event constants and automation chains.
- A single orchestrator entry point for registration.

## Scope

- Create `pipeline/flows/sources/coingecko_flow.py`.
- Create `pipeline/flows/transform_flow.py`.
- Create initial `pipeline/flows/master_flow.py` only if needed for local/manual orchestration.
- Create `pipeline/schedules/coingecko/events.py`.
- Create `pipeline/schedules/coingecko/deployments.py`.
- Create `pipeline/schedules/coingecko/automations.py`.
- Create shared deployment and automation helpers.
- Create `pipeline/schedules/orchestrator.py`.

## Acceptance Criteria

- A scheduled CoinGecko deployment can run the source flow.
- Successful EL emits a source completion event.
- The completion event can trigger a scoped dbt staging or mart flow.
- Flow retries and basic failure handling are configured.
- Adding a new source later requires only a new source schedule folder and one orchestrator registration line.

## Out of Scope

- Advanced alert routing.
- SLA monitoring.
- Streaming orchestration.
- Multi-source event dependency graphs beyond the first source.

## Grill Questions

- Should dbt run after every successful EL batch, or only when new rows were loaded?
- Should `master_flow.py` remain as a manual convenience, or should event chains be the only orchestration path?
- What event naming convention should be locked before adding more sources?
- How much Prefect state should be stored in custom metadata versus left in the Prefect UI?


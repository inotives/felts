# Phase 03 - dbt Transform Foundation

## Goal

Create the dbt project and prove the raw-to-staging-to-mart path for the first loaded source.

## Core Functionality

- dbt project under `pipeline/transforms/`.
- Raw views over loader tables.
- Staging models that unpack, type, and deduplicate source records.
- Initial intermediary and mart models for finance-oriented use cases.
- dbt tests for core assumptions.

## Scope

- Create `dbt_project.yml`, `profiles.yml`, and base macros.
- Create raw views for CoinGecko loader tables.
- Create `stg_coingecko__coins_markets`.
- Implement per-model dedup directly in staging SQL using the model's natural key and ordering rules.
- Create an initial finance mart such as market snapshot by asset.
- Add dbt `not_null`, `unique`, and accepted range tests where useful.

## Acceptance Criteria

- `dbt run` builds raw, staging, intermediary, and mart layers locally.
- Staging models contain no duplicate rows for their declared grain.
- The staging model keeps dedup logic readable in SQL.
- dbt tests catch null keys and obvious numeric quality failures.
- No transformation logic is moved into Python.

## Out of Scope

- SCD Type 2 dimensions unless the first mart requires them.
- Generic YAML-driven dedup configuration.
- Complex cross-source joins.
- Data quality history tables.

## Grill Questions

- What is the exact grain of `stg_coingecko__coins_markets`?
- Should market data use provider `last_updated_at`, ingestion `loaded_at`, or both in its grain?
- Which finance mart is most useful as the first consumer-facing model?
- Should staging models be views for speed of iteration, or incremental tables for volume realism?


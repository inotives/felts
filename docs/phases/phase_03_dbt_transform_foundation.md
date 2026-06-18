# Phase 03 - dbt Transform Foundation

## Goal

Create the dbt project and prove the raw-to-staging-to-mart path for the first loaded source.

## Core Functionality

- dbt project under top-level `transforms/`.
- dbt source definitions over loader-created raw tables.
- Staging models that unpack, type, and deduplicate source records.
- Initial mart models for finance-oriented reference use cases.
- dbt tests for core assumptions.

## Scope

- Create `dbt_project.yml`, `profiles.yml`, and base macros.
- Create dbt source definitions for CoinGecko loader tables.
- Create CoinGecko staging models for the Phase 02 loaded entities, prioritizing `coins_list`, `asset_platforms_list`, and `coins_markets`.
- Implement per-model dedup directly in staging SQL using the model's natural key and ordering rules.
- Create initial CoinGecko reference marts for coins and asset platforms.
- Add dbt `not_null`, `unique`, and accepted range tests where useful.

## Acceptance Criteria

- `make dbt-run` builds all Phase 03 dbt models from locally loaded CoinGecko raw tables.
- `make dbt-test` runs dbt tests for Phase 03 models.
- `make coingecko-transform` can load CoinGecko raw data, run dbt models, and run dbt tests locally.
- Staging models exist for all five Phase 02 CoinGecko entities.
- CoinGecko reference marts exist for coins and asset platforms.
- Staging models contain no duplicate rows for their declared grain.
- dbt tests catch null keys, duplicate grains, and obvious numeric quality failures.
- No transformation logic is moved into Python.

## Decisions

- Phase 03 uses top-level `transforms/` as the dbt project path.
- Staging models read directly from dbt `source()` definitions over loader-created raw tables, for example `source('coingecko', 'raw_coins_markets')`.
- Phase 03 does not add separate raw pass-through dbt views unless a concrete transform requirement appears.
- Provider-specific staging, intermediate, and mart models materialize into the same provider schema as the source raw tables. For CoinGecko, that means `coingecko.stg_coingecko__*`, `coingecko.int_coingecko__*`, and `coingecko.mart_coingecko__*` alongside `coingecko.raw_*`.
- Model name prefixes distinguish lifecycle layer inside the provider schema: `raw_`, `stg_`, `int_`, and `mart_`.
- Cross-provider marts are deferred; when needed, they should use a separate shared analytics schema rather than belonging to one provider schema.
- The first Phase 03 marts are CoinGecko reference marts for `coins_list` and `asset_platforms_list`, not a market snapshot mart.
- Phase 03 creates staging models for all five Phase 02 CoinGecko entities: `coins_list`, `asset_platforms_list`, `global`, `global_defi`, and `coins_markets`.
- Phase 03 creates marts only for `coins_list` and `asset_platforms_list`; `global`, `global_defi`, and `coins_markets` stop at staging unless needed for tests or lightweight intermediate validation.
- `stg_coingecko__global` and `stg_coingecko__global_defi` keep snapshot history in staging; Phase 03 does not create latest-only global marts or views.
- `stg_coingecko__coins_list` grain is one row per `coin_id`; dedup by CoinGecko `id`, ordered by `extracted_at desc, loaded_at desc`.
- `stg_coingecko__asset_platforms_list` grain is one row per `asset_platform_id`; dedup by CoinGecko `id`, ordered by `extracted_at desc, loaded_at desc`.
- `stg_coingecko__global` grain is one row per singleton snapshot; dedup by `source_record_id, extracted_at`, ordered by `loaded_at desc`.
- `stg_coingecko__global_defi` grain is one row per singleton snapshot; dedup by `source_record_id, extracted_at`, ordered by `loaded_at desc`.
- `stg_coingecko__coins_markets` grain is one row per `coin_id, observed_at`; dedup by CoinGecko `id, observed_at`, ordered by `extracted_at desc, loaded_at desc`.
- `mart_coingecko__coins` grain is one row per `coin_id`.
- `mart_coingecko__asset_platforms` grain is one row per `asset_platform_id`.
- Phase 03 reference marts are latest-state tables, not history tables.
- `mart_coingecko__coins` represents the latest known CoinGecko coin identity list.
- `mart_coingecko__asset_platforms` represents the latest known CoinGecko asset platform list.
- Phase 03 does not add SCD2 fields such as `valid_from`, `valid_to`, or `is_current`.
- Phase 03 staging models materialize as views.
- Phase 03 intermediate models, if needed, materialize as views.
- Phase 03 mart models materialize as tables.
- Phase 03 does not use incremental models yet.
- Phase 03 does not force intermediate models for reference marts when staging-to-mart is sufficient.
- The dbt project may include an intermediate folder/config so later reusable transforms have a clear home.
- Staging models normalize provider payload names into explicit analytical column names instead of exposing ambiguous provider names such as `id`, `symbol`, or `name`.
- Staging models filter to `is_valid = true`; invalid raw records remain available in raw source tables but do not enter staging or marts.
- Staging models include consistent raw metadata columns: `raw_record_id`, `source_record_id`, `extracted_at`, `loaded_at`, and `batch_id`.
- Staging models include the provider payload JSON as `raw_payload` for lineage and transform iteration.
- Mart models do not expose `raw_payload`.
- `stg_coingecko__coins_list` exposes columns such as `coin_id`, `coin_symbol`, and `coin_name`.
- `stg_coingecko__asset_platforms_list` exposes columns such as `asset_platform_id` and `asset_platform_name`.
- `stg_coingecko__coins_list` keeps `coin_symbol` as the provider value without case normalization.
- `asset_platform_id` stays provider-shaped exactly as CoinGecko sends it; Phase 03 does not normalize platform IDs into chain or network identifiers.
- Reference marts hide most raw ingestion metadata but retain lightweight lineage columns.
- `mart_coingecko__coins` exposes `coin_id`, `coin_symbol`, `coin_symbol_upper`, `coin_name`, `last_seen_at`, and `raw_record_id`.
- `mart_coingecko__asset_platforms` exposes `asset_platform_id`, `asset_platform_name`, `last_seen_at`, and `raw_record_id`.
- `last_seen_at` is derived from the selected staging row's `extracted_at`.
- `stg_coingecko__coins_list` tests include `not_null` and `unique` on `coin_id`, plus `not_null` on `coin_symbol` and `coin_name`.
- `stg_coingecko__asset_platforms_list` tests include `not_null` and `unique` on `asset_platform_id`, plus `not_null` on `asset_platform_name`.
- `stg_coingecko__coins_markets` tests include `not_null` on `coin_id` and `observed_at`, uniqueness on `coin_id, observed_at`, and a non-negative `current_price_usd` check when the value is present.
- `stg_coingecko__global` tests include `not_null` on `extracted_at` and `active_cryptocurrencies`.
- `stg_coingecko__global_defi` tests include `not_null` on `extracted_at`.
- `mart_coingecko__coins` tests include `not_null` and `unique` on `coin_id`.
- `mart_coingecko__asset_platforms` tests include `not_null` and `unique` on `asset_platform_id`.
- Phase 03 does not add external dbt packages such as `dbt_utils`.
- Where built-in dbt tests are insufficient, Phase 03 uses small local generic tests/macros.
- Phase 03 adds local generic dbt tests named `unique_combination_of_columns` and `expression_is_true`.
- `unique_combination_of_columns` supports uniqueness checks such as `coin_id, observed_at`.
- `expression_is_true` supports conditional quality checks such as `current_price_usd >= 0` when `current_price_usd is not null`.
- `dbt run` assumes Phase 02 CoinGecko raw tables already exist in local Postgres.
- Phase 03 adds a `make dbt-run` target that runs dbt transforms only.
- Phase 03 adds a convenience target such as `make coingecko-transform` that runs local raw loading before `dbt run` and `dbt test`.
- `make check` remains deterministic and does not depend on live CoinGecko API calls or preloaded raw source data.
- Phase 03 does not add an offline dbt fixture system for raw source tables.
- dbt model validation in Phase 03 is tied to locally loaded raw tables; fixture-based dbt CI is deferred to operational hardening.
- Phase 03 dbt files use this layout:
  - `transforms/models/sources/coingecko.yml`
  - `transforms/models/staging/coingecko/_coingecko__models.yml`
  - `transforms/models/staging/coingecko/stg_coingecko__coins_list.sql`
  - `transforms/models/staging/coingecko/stg_coingecko__asset_platforms_list.sql`
  - `transforms/models/staging/coingecko/stg_coingecko__global.sql`
  - `transforms/models/staging/coingecko/stg_coingecko__global_defi.sql`
  - `transforms/models/staging/coingecko/stg_coingecko__coins_markets.sql`
  - `transforms/models/marts/coingecko/_coingecko__models.yml`
  - `transforms/models/marts/coingecko/mart_coingecko__coins.sql`
  - `transforms/models/marts/coingecko/mart_coingecko__asset_platforms.sql`
  - `transforms/models/intermediate/coingecko/.gitkeep`
  - `transforms/macros/tests/`
- `stg_coingecko__coins_list` exposes: `coin_id`, `coin_symbol`, `coin_name`, `raw_record_id`, `source_record_id`, `extracted_at`, `loaded_at`, `batch_id`, `raw_payload`.
- `stg_coingecko__asset_platforms_list` exposes: `asset_platform_id`, `asset_platform_name`, `raw_record_id`, `source_record_id`, `extracted_at`, `loaded_at`, `batch_id`, `raw_payload`.
- `stg_coingecko__global` exposes: `source_record_id`, `active_cryptocurrencies`, `markets`, `total_market_cap_usd`, `extracted_at`, `loaded_at`, `raw_record_id`, `batch_id`, `raw_payload`.
- `stg_coingecko__global_defi` exposes: `source_record_id`, `defi_market_cap`, `eth_market_cap`, `defi_to_eth_ratio`, `extracted_at`, `loaded_at`, `raw_record_id`, `batch_id`, `raw_payload`.
- `stg_coingecko__coins_markets` exposes: `coin_id`, `coin_symbol`, `coin_name`, `current_price_usd`, `market_cap_usd`, `market_cap_rank`, `total_volume_usd`, `price_change_percentage_24h`, `circulating_supply`, `total_supply`, `observed_at`, `extracted_at`, `loaded_at`, `raw_record_id`, `source_record_id`, `batch_id`, `raw_payload`.
- `mart_coingecko__coins` exposes: `coin_id`, `coin_symbol`, `coin_symbol_upper`, `coin_name`, `last_seen_at`, `raw_record_id`.
- `mart_coingecko__asset_platforms` exposes: `asset_platform_id`, `asset_platform_name`, `last_seen_at`, `raw_record_id`.
- Mart models do not expose `batch_id`, `loaded_at`, or `raw_payload`.

## Out of Scope

- SCD Type 2 dimensions unless the first mart requires them.
- Generic YAML-driven dedup configuration.
- Complex cross-source joins.
- Data quality history tables.
- Offline dbt fixture system for raw source tables.

## Grill Questions

- What is the exact grain of `stg_coingecko__coins_markets`?
- Should market data use provider `last_updated_at`, ingestion `loaded_at`, or both in its grain?
- Which finance mart is most useful as the first consumer-facing model?
- Should staging models be views for speed of iteration, or incremental tables for volume realism?

---
id: task-0010
title: "Phase 11: broad CoinGecko mart completion"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-24
updated_on: 2026-07-24
priority: normal
parent: ""
depends_on:
  - task-0009
---






# Task

## Context

Task 0009 adds the Felts internal mapping layer. This task completes the missing
CoinGecko marts while keeping CoinGecko coverage broad.

Source of truth:

- `docs/phases/phase_11_analytical_marts_and_internal_assets.md`

## Goal

Add the missing consumer-facing CoinGecko fact and snapshot marts without filtering
to internally mapped assets.

## Scope

- Keep existing CoinGecko reference marts broad:
  - `coingecko.mart_coingecko__coins`
  - `coingecko.mart_coingecko__asset_platforms`
- Add missing broad CoinGecko marts:
  - `coingecko.mart_coingecko__coin_market_snapshots`
  - `coingecko.mart_coingecko__global_market_snapshots`
  - `coingecko.mart_coingecko__global_defi_snapshots`
- Each mart should select from its matching staging model.
- Preserve staging model grain and provider-native identifiers.
- Keep useful lineage fields already present in staging.
- Add model YAML descriptions and dbt tests.
- Do not join to Felts internal mapping marts in this task.
- Do not drop unmapped CoinGecko rows.

## Planner Notes

The critical behavior is broad coverage. Internal identity is opt-in through joins
against the `felts` schema; CoinGecko marts remain provider-native.

## Implementation Plan

1. Inspect existing CoinGecko staging models and reference mart style.
2. Add the three missing CoinGecko mart SQL models.
3. Extend CoinGecko model YAML with descriptions and grain tests.
4. Run focused dbt run/test selectors for CoinGecko marts if local Postgres is
   available; otherwise record the skipped DB prerequisite.

## Acceptance Criteria

- [ ] Existing CoinGecko reference marts still build.
- [ ] `mart_coingecko__coin_market_snapshots` builds from
  `stg_coingecko__coins_markets`.
- [ ] `mart_coingecko__global_market_snapshots` builds from
  `stg_coingecko__global`.
- [ ] `mart_coingecko__global_defi_snapshots` builds from
  `stg_coingecko__global_defi`.
- [ ] CoinGecko mart rows are not filtered by Felts internal mappings.
- [ ] CoinGecko marts retain provider-native identifiers and lineage fields.
- [ ] Model YAML documents each new mart and tests its declared grain.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes
- Implemented the three missing broad CoinGecko marts as direct selects from the
  matching staging models, preserving provider-native identifiers and lineage fields.
- Extended CoinGecko model YAML with mart descriptions plus grain tests for market
  snapshots and global snapshot marts.
- Verification on 2026-07-23:
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache uv run dbt parse --project-dir transforms --profiles-dir transforms` succeeded.
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache uv run dbt run --project-dir transforms --profiles-dir transforms --select mart_coingecko__coins mart_coingecko__asset_platforms mart_coingecko__coin_market_snapshots mart_coingecko__global_market_snapshots mart_coingecko__global_defi_snapshots` failed at Postgres connect with `Operation not permitted` to `localhost:5432` in the sandbox.
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache uv run dbt test --project-dir transforms --profiles-dir transforms --select mart_coingecko__coins mart_coingecko__asset_platforms mart_coingecko__coin_market_snapshots mart_coingecko__global_market_snapshots mart_coingecko__global_defi_snapshots` failed at the same Postgres connect step.

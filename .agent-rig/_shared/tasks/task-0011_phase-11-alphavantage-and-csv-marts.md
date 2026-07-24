---
id: task-0011
title: "Phase 11: Alpha Vantage and CSV marts"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-24
updated_on: 2026-07-24
priority: normal
parent: ""
depends_on:
  - task-0010
---






# Task

## Context

Tasks 0009 and 0010 add Felts internal mapping marts and complete CoinGecko mart
coverage. This task adds source-owned marts for the remaining already staged
sources.

Source of truth:

- `docs/phases/phase_11_analytical_marts_and_internal_assets.md`

## Goal

Add consumer-facing mart tables for Alpha Vantage daily prices, CSV OHLCV candles,
and CSV FRED observations.

## Scope

- Configure source-owned mart schemas as needed:
  - `marts/alphavantage` -> schema `alphavantage`
  - `marts/csv_import` -> schema `csv_import`
- Add missing Alpha Vantage and CSV marts:
  - `alphavantage.mart_alphavantage__daily_prices`
  - `csv_import.mart_csv_import__ohlcv`
  - `csv_import.mart_csv_import__fred_observations`
- Each mart should select from its matching staging model.
- Preserve staging model grain and source-native identifiers.
- Keep useful lineage fields already present in staging.
- Add model YAML descriptions and dbt tests.
- Do not add derived metrics such as returns, moving averages, or signals.
- Do not create a canonical cross-source price mart.

## Planner Notes

This is a mart completion task, not an analytics layer. Keep the marts as typed
consumer tables over staging.

## Implementation Plan

1. Inspect existing Alpha Vantage and CSV staging model grains.
2. Add mart SQL models for daily prices, OHLCV, and FRED observations.
3. Add model YAML descriptions and declared-grain tests.
4. Run focused dbt run/test selectors for the new marts if local Postgres is
   available; otherwise record the skipped DB prerequisite.

## Acceptance Criteria

- [ ] `mart_alphavantage__daily_prices` builds from
  `stg_alphavantage__time_series_daily`.
- [ ] `mart_csv_import__ohlcv` builds from `stg_csv_import__ohlcv`.
- [ ] `mart_csv_import__fred_observations` builds from
  `stg_csv_import__fred_series`.
- [ ] Each mart preserves its staging grain.
- [ ] Each mart retains source-native identifiers and lineage fields.
- [ ] Model YAML documents each new mart and tests its declared grain.
- [ ] No derived metrics or canonical cross-source mart are added.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes
- Implemented the missing Alpha Vantage and CSV marts as direct selects from their
  matching staging models, preserving source-native identifiers and lineage fields.
- Added mart schema config for `marts/alphavantage` and `marts/csv_import`.
- Extended the Alpha Vantage and CSV model YAML files with mart descriptions and
  grain tests.
- Verification on 2026-07-24:
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache uv run dbt parse --project-dir transforms --profiles-dir transforms` succeeded.
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache uv run dbt run --project-dir transforms --profiles-dir transforms --select mart_alphavantage__daily_prices mart_csv_import__ohlcv mart_csv_import__fred_observations` failed at Postgres connect with `Operation not permitted` to `localhost:5432` in the sandbox.
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache uv run dbt test --project-dir transforms --profiles-dir transforms --select mart_alphavantage__daily_prices mart_csv_import__ohlcv mart_csv_import__fred_observations` failed at the same Postgres connect step.

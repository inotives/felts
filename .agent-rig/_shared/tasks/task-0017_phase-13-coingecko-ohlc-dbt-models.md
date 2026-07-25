---
id: task-0017
title: "Phase 13: CoinGecko OHLC dbt models"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-25
priority: normal
parent: ""
depends_on:
  - task-0016
---

# Task

## Context

Task 0016 adds raw CoinGecko OHLC capture. This task models that raw entity through
dbt.

Source of truth:

- `docs/phases/phase_13_coingecko_ohlc_capture.md`

## Goal

Create staging and mart models for CoinGecko OHLC candles at the provider candle
grain.

## Scope

- Add source definition for `coingecko.raw_coins_ohlc`.
- Add staging model `stg_coingecko__coins_ohlc`.
- Add mart model `mart_coingecko__coin_ohlc_candles`.
- Staging and mart grain:
  - `coin_id`
  - `vs_currency`
  - `observed_at`
- Expose OHLC fields and raw evidence columns consistent with existing CoinGecko
  models.
- Add dbt docs/tests for not-null fields and candle-grain uniqueness.

## Planner Notes

Keep this provider-shaped. Do not join to Felts internal mappings and do not add
volume.

## Implementation Plan

1. Add `raw_coins_ohlc` to the CoinGecko source YAML.
2. Add staging SQL that extracts typed fields from raw payload and deduplicates by
   `coin_id, vs_currency, observed_at`, keeping the latest raw load.
3. Add mart SQL that exposes the staging grain.
4. Add model YAML documentation and tests.
5. Run focused dbt parse/run/test selectors when local dbt dependencies are
   available.

## Acceptance Criteria

- [ ] `source('coingecko', 'raw_coins_ohlc')` is defined.
- [ ] `stg_coingecko__coins_ohlc` builds from raw OHLC records.
- [ ] `mart_coingecko__coin_ohlc_candles` builds from staging.
- [ ] The mart does not expose volume.
- [ ] dbt tests cover not-null `coin_id`, `vs_currency`, `observed_at`, `open`,
      `high`, `low`, and `close`.
- [ ] dbt tests cover uniqueness for `coin_id, vs_currency, observed_at`.
- [ ] Focused dbt verification or blocker details are recorded in `## Notes`.

## Notes

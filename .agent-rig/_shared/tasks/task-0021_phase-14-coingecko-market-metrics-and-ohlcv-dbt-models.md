---
id: task-0021
title: "Phase 14: CoinGecko market metrics and OHLCV dbt models"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on:
  - task-0020
---


# Task

## Context

Task 0020 adds the CoinGecko `coins_market_chart` raw entity and updates OHLC to
daily interval. This task models those daily market metrics and derives daily
OHLCV.

Source of truth:

- `docs/phases/phase_14_coingecko_daily_market_metrics_and_ohlcv.md`

## Goal

Create dbt staging and mart models for CoinGecko daily market metrics, then join
them with daily OHLC candles into a derived OHLCV mart.

## Scope

- Add source definition for `coingecko.raw_coins_market_chart`.
- Add staging model `stg_coingecko__coins_market_chart`.
- Staging grain:
  - `coin_id`
  - `vs_currency`
  - `interval`
  - `observed_at`
- Add mart model `mart_coingecko__coin_daily_market_metrics`.
- Add derived mart model `mart_coingecko__coin_ohlcv_daily`.
- Join OHLC to daily market metrics by:
  - `coin_id`
  - `vs_currency`
  - `observed_at`
- Expose OHLCV fields:
  - `coin_id`
  - `vs_currency`
  - `observed_at`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
  - `market_cap`
  - `price`
  - raw lineage columns needed by existing mart patterns
- Add dbt docs/tests for not-null fields and model-grain uniqueness.

## Planner Notes

Keep the marts provider-shaped. Do not join to Felts internal mappings.

Use `coins_market_chart` as daily volume truth. Do not derive daily volume from
`coins_markets`.

## Implementation Plan

1. Add `raw_coins_market_chart` to the CoinGecko source YAML.
2. Add staging SQL that extracts typed fields from raw market-chart payloads and
   deduplicates by `coin_id, vs_currency, interval, observed_at`.
3. Add the daily market metrics mart as a thin provider-shaped mart.
4. Add the OHLCV mart as a thin join from daily OHLC to daily market metrics.
5. Add model YAML documentation and tests.
6. Run focused dbt parse/run/test selectors when local dbt dependencies are
   available.

## Acceptance Criteria

- [ ] `source('coingecko', 'raw_coins_market_chart')` is defined.
- [ ] `stg_coingecko__coins_market_chart` builds from raw market-chart records.
- [ ] `mart_coingecko__coin_daily_market_metrics` builds from staging.
- [ ] `mart_coingecko__coin_ohlcv_daily` builds by joining OHLC and market
      metrics.
- [ ] Daily metrics tests cover uniqueness for
      `coin_id, vs_currency, interval, observed_at`.
- [ ] OHLCV tests cover uniqueness for `coin_id, vs_currency, observed_at`.
- [ ] Not-null tests cover the required daily metrics and OHLCV fields.
- [ ] The OHLCV mart does not use `coins_markets.total_volume_usd`.
- [ ] Focused dbt verification or blocker details are recorded in `## Notes`.

## Notes

- Added `coingecko.raw_coins_market_chart` source metadata and new staging model
  `stg_coingecko__coins_market_chart`.
- Added new marts:
  `mart_coingecko__coin_daily_market_metrics` and
  `mart_coingecko__coin_ohlcv_daily`.
- Updated OHLC staging and mart models to carry the Phase 14 `interval` field.
  For backward compatibility with pre-Phase-14 local raw rows that do not have
  `payload.interval`, staging now surfaces `provider_default` instead of `null`.
- The OHLCV mart joins `stg_coingecko__coins_ohlc` to
  `stg_coingecko__coins_market_chart` on `coin_id`, `vs_currency`, and
  `observed_at`, and uses `market_chart.total_volume` as `volume`.
- Live note from Monday, July 27, 2026: local `./.venv/bin/felts coingecko run --entities coins_ohlc coins_market_chart`
  failed on `coins_ohlc` because CoinGecko returned `400 Bad Request` for
  `/coins/{id}/ohlc?...&interval=daily`. The dbt verification below therefore
  used fresh live `coins_market_chart` raw rows plus the existing local OHLC
  raw table.
- Verification:
  - `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms`
    -> passed
  - `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
    -> `PASS=3 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=3`
  - `./.venv/bin/felts coingecko run --entities coins_market_chart`
    -> `source=coingecko entity=coins_market_chart extracted=270 inserted=270 skipped_duplicate=0 invalid=0 failed=0`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    -> `PASS=5 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=5`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    -> `PASS=45 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=45`

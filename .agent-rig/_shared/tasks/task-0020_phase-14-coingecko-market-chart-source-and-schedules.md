---
id: task-0020
title: "Phase 14: CoinGecko market-chart source and schedules"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on: []
---


# Task

## Context

Phase 14 adds daily CoinGecko historical market metrics, corrects OHLC capture to
daily grain, and schedules the related CoinGecko captures.

Source of truth:

- `docs/phases/phase_14_coingecko_daily_market_metrics_and_ohlcv.md`

## Goal

Add the `coins_market_chart` CoinGecko raw extraction path, update OHLC requests
to daily interval, and schedule OHLC, market chart, and broad market snapshots.

## Scope

- Add `coins_market_chart` to CoinGecko supported entities and dbt selector
  mapping.
- Fetch `/coins/{coin_id}/market_chart` for mapped CoinGecko assets with:
  - `vs_currency` from existing CoinGecko market currency settings;
  - `days=90`;
  - `interval=daily`.
- Keep default CoinGecko IDs loaded from
  `transforms/seeds/felts/asset_provider_mappings.csv` where
  `provider_source=coingecko`.
- Flatten each market-chart response into one raw object payload per timestamp:
  - `coin_id`
  - `vs_currency`
  - `days`
  - `interval`
  - `timestamp_ms`
  - `price`
  - `market_cap`
  - `total_volume`
- Set `observed_at` from `timestamp_ms` as UTC.
- Set market-chart `source_record_id` to
  `coin_id|vs_currency|interval|timestamp_ms`.
- Update `coins_ohlc` requests to include `interval=daily`.
- Add `interval` to the OHLC raw payload.
- Keep OHLC `source_record_id` as `coin_id|vs_currency|timestamp_ms`.
- Add raw validation schema coverage for `coins_market_chart` and the OHLC
  interval field.
- Schedule daily deployments:
  - `coins_ohlc`: `0 3 * * *`
  - `coins_market_chart`: `15 3 * * *`
  - `coins_markets`: `30 3 * * *`
- Wire raw completion events to:
  - `coins_ohlc`: `stg_coingecko__coins_ohlc+`
  - `coins_market_chart`: `stg_coingecko__coins_market_chart+`
  - `coins_markets`: `stg_coingecko__coins_markets+`

## Planner Notes

Do not use `/coins/markets` `total_volume` as daily OHLCV volume. It remains a
broad current market snapshot capture, not the historical daily volume source.

Do not add broad all-CoinGecko per-coin market-chart capture.

## Implementation Plan

1. Extend CoinGecko constants, schema registration, extractor dispatch, runner
   wiring, schedules, and event selector mapping.
2. Add market-chart response parsing that joins `prices`, `market_caps`, and
   `total_volumes` by timestamp.
3. Update OHLC request parameters and raw payloads for `interval=daily`.
4. Add or update focused unit tests for request params, parsed payloads,
   malformed response rejection, duplicate-stable source IDs, runner
   registration, event selectors, and deployment schedules.
5. Run focused CoinGecko unit tests.

## Acceptance Criteria

- [ ] `coins_market_chart` is accepted by the CoinGecko runner.
- [ ] Market-chart requests use `/coins/{coin_id}/market_chart`,
      `vs_currency`, `days=90`, and `interval=daily`.
- [ ] OHLC requests include `interval=daily`.
- [ ] Market-chart payloads contain the Phase 14 raw fields.
- [ ] OHLC payloads include `interval`.
- [ ] Market-chart `observed_at` is derived from `timestamp_ms`.
- [ ] Market-chart `source_record_id` is
      `coin_id|vs_currency|interval|timestamp_ms`.
- [ ] OHLC `source_record_id` remains `coin_id|vs_currency|timestamp_ms`.
- [ ] Bad market-chart response shapes raise `ExtractionError`.
- [ ] Daily deployment schedules match `03:00`, `03:15`, and `03:30` UTC.
- [ ] Event payload selectors are wired for `coins_ohlc`,
      `coins_market_chart`, and `coins_markets`.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

- Added `coins_market_chart` to CoinGecko supported entities, raw schema
  registration, event selector mapping, and deployment schedule wiring.
- Added `/coins/{coin_id}/market_chart` extraction for mapped CoinGecko assets
  using `vs_currency`, `days=90`, and `interval=daily`, with flattened raw
  payload fields:
  `coin_id|vs_currency|days|interval|timestamp_ms|price|market_cap|total_volume`.
- Updated `coins_ohlc` requests to send `interval=daily` and to include
  `interval` in the raw payload while keeping raw identity as
  `coin_id|vs_currency|timestamp_ms`.
- Added focused tests for market-chart parsing, malformed response rejection,
  schema registration, runner support, event selectors, and staggered Phase 14
  schedules.
- Verification:
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
    -> `31 passed in 2.84s`
  - `./.venv/bin/ruff check src/felts/sources/coingecko tests/unit/sources/coingecko`
    -> `All checks passed!`
  - `./.venv/bin/ruff format --check src/felts/sources/coingecko tests/unit/sources/coingecko`
    -> `15 files already formatted`

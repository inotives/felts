---
id: task-0016
title: "Phase 13: CoinGecko OHLC source capture"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-26
priority: normal
parent: ""
depends_on: []
---



# Task

## Context

Phase 13 adds true CoinGecko OHLC candle capture for mapped internal crypto assets.

Source of truth:

- `docs/phases/phase_13_coingecko_ohlc_capture.md`

## Goal

Add the `coins_ohlc` CoinGecko entity and raw extraction path with stable duplicate
identity for daily rolling 90-day captures.

## Scope

- Add `coins_ohlc` to CoinGecko supported entities and dbt selector mapping.
- Fetch `/coins/{coin_id}/ohlc` with:
  - `vs_currency` from existing CoinGecko market currency settings;
  - `days=90`;
  - no `interval` parameter.
- Read default CoinGecko IDs from
  `transforms/seeds/felts/asset_provider_mappings.csv` where
  `provider_source=coingecko`.
- Convert provider array rows into raw object payload fields:
  - `coin_id`
  - `vs_currency`
  - `days`
  - `timestamp_ms`
  - `open`
  - `high`
  - `low`
  - `close`
- Set `observed_at` from `timestamp_ms` as UTC candle close time.
- Set `source_record_id` to `coin_id|vs_currency|timestamp_ms`.
- Add raw validation schema coverage for the new payload.
- Add a daily Prefect schedule for `coins_ohlc` at `0 3 * * *` UTC.
- Keep raw completion events wired to `stg_coingecko__coins_ohlc+`.

## Planner Notes

Do not include `days` in `source_record_id`. Rolling windows must skip already-seen
candles even if the capture window changes later.

Do not add market-chart capture, volume, interval overrides, or broad all-coin
capture in this task.

## Implementation Plan

1. Extend CoinGecko constants, schema registration, extractor dispatch, and runner
   wiring for `coins_ohlc`.
2. Add a small helper for reading mapped CoinGecko IDs from the seed CSV.
3. Add OHLC response parsing with shape validation and timestamp conversion.
4. Add or update unit tests for request params, mapped ID defaults, parsed payloads,
   malformed response rejection, duplicate-stable source IDs, runner registration,
   event selector, and daily deployment schedule.
5. Run focused CoinGecko unit tests.

## Acceptance Criteria

- [ ] `coins_ohlc` is accepted by the CoinGecko runner.
- [ ] Default extraction reads only `provider_source=coingecko` seed mappings.
- [ ] Requests use `/coins/{coin_id}/ohlc`, `vs_currency`, and `days=90`.
- [ ] Requests do not send `interval`.
- [ ] Parsed raw payloads contain the Phase 13 fields.
- [ ] `observed_at` is derived from `timestamp_ms`.
- [ ] `source_record_id` is `coin_id|vs_currency|timestamp_ms`.
- [ ] Bad OHLC response shapes raise `ExtractionError`.
- [ ] `coins_ohlc` deployment has cron `0 3 * * *` UTC.
- [ ] Event payload selector is `stg_coingecko__coins_ohlc+`.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

- Added `coins_ohlc` to the CoinGecko source constants, selector map, supported
  entities, daily schedules, and event selector mapping.
- Added seed-backed default CoinGecko ID loading in
  `src/felts/sources/coingecko/extractor.py` from
  `transforms/seeds/felts/asset_provider_mappings.csv`, filtered to
  `provider_source=coingecko` and de-duplicated by `provider_asset_id`.
- Added `/coins/{coin_id}/ohlc` extraction with:
  - `vs_currency` from the existing CoinGecko market currency setting
  - `days=90`
  - no `interval` parameter
  - raw object payload fields `coin_id`, `vs_currency`, `days`, `timestamp_ms`,
    `open`, `high`, `low`, and `close`
  - `observed_at` derived from `timestamp_ms`
  - `source_record_id` set to `coin_id|vs_currency|timestamp_ms`
- Added raw validation schema coverage for `coins_ohlc`.
- Added focused unit coverage for mapped ID defaults, duplicate-safe identity,
  malformed OHLC responses, runner support, daily deployment schedule, and event
  selector wiring.
- Verification on 2026-07-26:
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py -q` -> `11 passed in 0.14s`
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_runner.py -q` -> `6 passed in 0.14s`
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_deployments.py -q` -> `2 passed in 1.15s`
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_events.py -q` -> `4 passed in 0.71s`
  - `./.venv/bin/ruff check src/felts/sources/coingecko tests/unit/sources/coingecko` -> `All checks passed!`
  - `./.venv/bin/ruff format --check src/felts/sources/coingecko tests/unit/sources/coingecko` -> `15 files already formatted`
  - `./.venv/bin/python -m mypy src/felts/sources/coingecko` -> `Success: no issues found in 10 source files`

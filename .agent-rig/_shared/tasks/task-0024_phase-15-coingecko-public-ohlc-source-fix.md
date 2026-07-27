---
id: task-0024
title: "Phase 15: CoinGecko public OHLC source fix"
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

Phase 15 fixes the live public CoinGecko `coins_ohlc` failure from Phase 14.

Source of truth:

- `docs/phases/phase_15_coingecko_public_ohlc_rollup_fix.md`

## Goal

Make `coins_ohlc` extraction compatible with the public CoinGecko API by using
30-day auto-granularity OHLC and no explicit interval request parameter.

## Scope

- Change OHLC extraction from `days=90` to `days=30`.
- Remove the OHLC request `interval` parameter.
- Store raw OHLC payload `interval` as `4h`.
- Keep OHLC raw `source_record_id` as `coin_id|vs_currency|timestamp_ms`.
- Keep `coins_market_chart` unchanged at `days=90&interval=daily`.
- Keep existing `coins_ohlc` scheduling and event selector behavior.
- Update raw validation schema coverage for the corrected OHLC payload.
- Update focused unit tests for OHLC request parameters and payload shape.

## Planner Notes

Do not add paid-plan CoinGecko URL/key support in this task.

Do not delete old raw rows. Raw remains append-only.

## Implementation Plan

1. Update the CoinGecko extractor defaults and OHLC request parameters.
2. Update OHLC raw payload construction to emit `days=30` and `interval=4h`.
3. Keep market-chart days and interval behavior unchanged.
4. Update focused source, runner, schema, schedule, and event tests.
5. Run focused CoinGecko unit tests.

## Acceptance Criteria

- [ ] `coins_ohlc` requests send `days=30`.
- [ ] `coins_ohlc` requests do not send `interval`.
- [ ] OHLC raw payloads store `interval = 4h`.
- [ ] OHLC raw identity remains `coin_id|vs_currency|timestamp_ms`.
- [ ] `coins_market_chart` still sends `days=90&interval=daily`.
- [ ] Existing `coins_ohlc` deployment schedule remains unchanged.
- [ ] Existing `coins_ohlc` event selector remains `stg_coingecko__coins_ohlc+`.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

- Updated `src/felts/sources/coingecko/extractor.py` so `coins_ohlc` now uses
  `days=30` with no request `interval`, while `coins_market_chart` keeps its
  separate `days=90&interval=daily` request contract.
- OHLC raw payload construction now stores `interval = 4h` while keeping
  `source_record_id = coin_id|vs_currency|timestamp_ms`.
- Updated focused OHLC extractor and runner tests to cover the corrected public
  API request shape and payload fields.
- Verification:
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
  - `31 passed in 1.26s`
- Reviewer verification on Monday, July 27, 2026:
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
  - `31 passed in 1.17s`
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/felts coingecko run --entities coins_ohlc`
  - `source=coingecko entity=coins_ohlc extracted=540 inserted=540 skipped_duplicate=0 invalid=0 failed=0`
  - Raw warehouse spot-check after the live run confirmed Phase 15 rows persist
    with `days=30`, `interval=4h`, and unchanged
    `source_record_id=coin_id|usd|timestamp_ms` shape.

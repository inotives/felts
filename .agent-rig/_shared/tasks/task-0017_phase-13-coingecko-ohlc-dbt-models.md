---
id: task-0017
title: "Phase 13: CoinGecko OHLC dbt models"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-25
updated_on: 2026-07-26
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

- Added `coingecko.raw_coins_ohlc` to `transforms/models/sources/coingecko.yml`.
- Added `transforms/models/staging/coingecko/stg_coingecko__coins_ohlc.sql` with:
  - `where is_valid`
  - typed extraction of `coin_id`, `vs_currency`, `days`, `timestamp_ms`, `open`,
    `high`, `low`, and `close`
  - raw evidence columns consistent with existing CoinGecko staging models
  - deduplication by `coin_id, vs_currency, observed_at`, keeping the latest raw
    load by `extracted_at desc, loaded_at desc`
- Added `transforms/models/marts/coingecko/mart_coingecko__coin_ohlc_candles.sql`
  as a thin provider-shaped mart over the staging grain. It does not expose
  volume and does not join to Felts internal mappings.
- Added dbt docs/tests in `transforms/models/staging/coingecko/_coingecko__models.yml`
  for not-null `coin_id`, `vs_currency`, `observed_at`, `open`, `high`, `low`,
  and `close`, plus uniqueness on `coin_id, vs_currency, observed_at` for both
  staging and mart.
- Verification on Sunday, July 26, 2026:
  - `./.venv/bin/dbt parse --project-dir transforms --profiles-dir transforms` -> passed
  - Initial sandboxed `dbt run/test` attempts failed because sandbox access to local
    Postgres on `localhost:5432` is blocked.
  - First unsandboxed `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+`
    failed because local relation `coingecko.raw_coins_ohlc` did not yet exist.
  - `./.venv/bin/felts coingecko run --entities coins_ohlc` -> `source=coingecko`,
    `entity=coins_ohlc extracted=69 inserted=69 skipped_duplicate=0 invalid=0 failed=0`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+`
    -> built `coingecko.stg_coingecko__coins_ohlc` and
    `coingecko.mart_coingecko__coin_ohlc_candles` successfully with `SELECT 69`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+`
    -> `PASS=16 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=16`

# Phase 15 - CoinGecko Public OHLC Rollup Fix

## Goal

Fix the Phase 14 live `coins_ohlc` failure by returning OHLC capture to
CoinGecko public-API-compatible auto granularity, then derive daily OHLC in dbt
from provider 4-hour candles.

Phase 15 keeps the Phase 14 daily market-chart metrics work, but changes the
daily OHLCV path so it no longer depends on `/coins/{id}/ohlc?interval=daily`.
CoinGecko currently rejects that explicit interval override on the public API.

## Context

- Felts is implemented through Phase 14.
- Phase 14 added `coins_market_chart`, daily market metrics, and derived OHLCV
  marts.
- Phase 14 also changed `coins_ohlc` to request `days=90&interval=daily`.
- Task 0023 found a live public API failure:
  - `GET /coins/bitcoin/ohlc?vs_currency=usd&days=90&interval=daily`
  - status `400`
  - body `{"error":"invalid interval parameter"}`
- Live comparison showed public `/coins/{id}/ohlc?days=90` works without
  `interval`, but returns 4-day candles.
- CoinGecko documents automatic OHLC granularity:
  - `1-2` days: 30-minute candles
  - `3-30` days: 4-hour candles
  - `31+` days: 4-day candles
- CoinGecko documents explicit `interval=daily` and `interval=hourly` as paid-plan
  subscriber features.

Provider reference:

- <https://docs.coingecko.com/reference/coins-id-ohlc>

## Decisions

- Keep this phase focused on the public API OHLC fix and dbt daily rollup.
- Change CoinGecko OHLC extraction from `days=90` to `days=30`.
- Remove the OHLC request `interval` parameter.
- Accept CoinGecko's public API auto granularity for `days=30`, which is 4-hour
  OHLC candles.
- Store raw OHLC payload `interval` as `4h` to make the inferred provider candle
  width explicit.
- Keep OHLC raw `source_record_id` as:

  ```text
  coin_id|vs_currency|timestamp_ms
  ```

- Keep `coins_market_chart` at `days=90&interval=daily`.
- Keep `stg_coingecko__coins_ohlc` provider-shaped at one row per 4-hour candle.
- Add an intermediate daily OHLC rollup model after staging.
- Use UTC candle close date from `observed_at` as the daily rollup date.
- Change `coingecko.mart_coingecko__coin_ohlc_candles` to serve daily rollup
  candles from the intermediate model instead of serving staging rows directly.
- Keep `coingecko.mart_coingecko__coin_ohlcv_daily` as the public daily OHLCV
  mart, joined from daily OHLC rollups and daily market-chart metrics.
- Do not expose the intermediate rollup model through MCP.
- Do not delete or migrate old Phase 14 raw rows. Raw records remain append-only.

## Raw Contract

OHLC extraction should call:

```text
/coins/{coin_id}/ohlc?vs_currency=<currency>&days=30
```

Do not send `interval`.

Each provider OHLC array row should continue to be flattened into a raw object
payload with:

- `coin_id`
- `vs_currency`
- `days`
- `interval`
- `timestamp_ms`
- `open`
- `high`
- `low`
- `close`

For Phase 15 records:

- `days` is `30`
- `interval` is `4h`
- `observed_at` is the UTC timestamp converted from `timestamp_ms`
- `source_record_id` is `coin_id|vs_currency|timestamp_ms`

The staging model should remain compatible with older raw rows, but corrected
daily rollups must filter to Phase 15-compatible rows so older Phase 14
`interval=daily` or `days=90` rows do not affect daily output.

## Transform Contract

Keep staging model:

- `coingecko.stg_coingecko__coins_ohlc`

Staging grain remains one row per:

```text
coin_id, vs_currency, observed_at
```

Staging represents provider 4-hour OHLC candles for corrected Phase 15 records.

Add intermediate model:

- `coingecko.int_coingecko__coin_ohlc_daily_rollups`

Intermediate grain is one row per:

```text
coin_id, vs_currency, observed_at
```

For the intermediate model, `observed_at` should be the UTC daily rollup date as a
timestamp, derived from the 4-hour candle close date.

Daily rollup rules:

- `open`: first 4-hour candle open of the UTC close-date
- `high`: max high of the UTC close-date
- `low`: min low of the UTC close-date
- `close`: last 4-hour candle close of the UTC close-date

The intermediate model should filter source rows to:

- `days = 30`
- `interval = '4h'`

Update mart model:

- `coingecko.mart_coingecko__coin_ohlc_candles`

The OHLC mart should read from `int_coingecko__coin_ohlc_daily_rollups` and expose
daily rollup candles.

Update derived mart:

- `coingecko.mart_coingecko__coin_ohlcv_daily`

The OHLCV mart should join daily OHLC rollups to
`stg_coingecko__coins_market_chart` by:

```text
coin_id, vs_currency, observed_at
```

`coins_market_chart` remains the source of `volume`, `market_cap`, and `price`.

## MCP Access Contract

Keep the committed MCP allowlist unchanged.

The existing public MCP marts remain:

- `coingecko.mart_coingecko__coin_ohlc_candles`
- `coingecko.mart_coingecko__coin_ohlcv_daily`

Do not allowlist:

- `coingecko.int_coingecko__coin_ohlc_daily_rollups`
- raw OHLC relations
- staging OHLC relations

## Acceptance Criteria

- `coins_ohlc` requests use `days=30`.
- `coins_ohlc` requests do not include an `interval` parameter.
- OHLC raw payloads store `interval = 4h`.
- OHLC raw payloads keep duplicate-safe source identity
  `coin_id|vs_currency|timestamp_ms`.
- `coins_market_chart` still requests `days=90&interval=daily`.
- `stg_coingecko__coins_ohlc` keeps provider 4-hour candle grain for corrected
  rows.
- `int_coingecko__coin_ohlc_daily_rollups` builds daily OHLC from 4-hour candles.
- `mart_coingecko__coin_ohlc_candles` serves daily rollup candles from the
  intermediate model.
- `mart_coingecko__coin_ohlcv_daily` joins daily OHLC rollups to daily
  market-chart metrics.
- MCP allowlist does not expose the intermediate model.
- A live public API smoke run for `coins_ohlc` passes.

## Verification

Run fast checks:

```bash
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/python -m mypy
./.venv/bin/pytest tests/unit
```

Run dbt checks:

```bash
dbt seed
dbt run --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+
dbt test --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+
```

Run the required live smoke check:

```bash
./.venv/bin/felts coingecko run --entities coins_ohlc
```

If sandboxed dbt cannot connect to local Postgres on `localhost:5432`, rerun dbt
outside the sandbox and record that in task notes.

## Out of Scope Until Explicitly Approved

- Switching to CoinGecko paid-plan OHLC interval support.
- Adding a paid-plan base URL/key path.
- Deleting or mutating existing raw OHLC rows.
- Exposing intermediate dbt models through MCP.
- Changing `coins_market_chart` away from `days=90&interval=daily`.
- Intraday OHLCV marts.
- Historical range backfill.
- Running `scripts/update-prod-data-access.sh` against production.

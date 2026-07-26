# Phase 13 - CoinGecko OHLC Capture

## Goal

Add true CoinGecko OHLC candle capture for mapped internal crypto assets, model
those candles through dbt, and expose the resulting mart through the existing
mart-first MCP production-data allowlist.

Phase 13 captures OHLC, not OHLCV. CoinGecko's OHLC endpoint returns open, high,
low, and close values only. It does not return volume, so this phase must not
synthesize volume or name the modeled output OHLCV.

## Context

- Felts is implemented through Phase 12.
- Phase 11 added broad source-owned CoinGecko marts and Felts-owned internal asset
  mapping marts.
- Phase 12 exposed the Phase 11 mart surface through the schema-qualified MCP
  allowlist.
- CoinGecko currently ingests coin lists, asset platform lists, broad market
  snapshots, global market snapshots, and global DeFi snapshots.
- Existing OHLCV support is CSV import only.
- CoinGecko historical OHLC capture is per coin, so broad all-coin capture is too
  expensive and rate-limit prone for the first implementation.

## Decisions

- Add a new CoinGecko entity named `coins_ohlc`.
- Use CoinGecko's true OHLC endpoint, not the market-chart endpoint.
- Fetch `/coins/{coin_id}/ohlc`.
- Use the existing CoinGecko `vs_currency` setting, currently
  `COINGECKO_MARKETS_VS_CURRENCY`, for OHLC requests.
- Default to `days=90`.
- Do not pass an `interval` parameter in Phase 13.
- Accept CoinGecko provider auto granularity.
- Default CoinGecko IDs come from
  `transforms/seeds/felts/asset_provider_mappings.csv` where
  `provider_source=coingecko`.
- Read the mapping seed directly for source extraction defaults. Do not make raw
  ingestion depend on a dbt mart already existing in the warehouse.
- Do not capture every CoinGecko coin in Phase 13.
- Add a scheduled Prefect deployment for `coins_ohlc`.
- Schedule the deployment daily at `03:00:00` UTC, expressed as cron
  `0 3 * * *`.
- Raw completion events for `coins_ohlc` should trigger dbt selector
  `stg_coingecko__coins_ohlc+`.
- Add the resulting OHLC mart to the production MCP allowlist.
- Do not run production access reconciliation during implementation close-out.

## Raw Contract

Each CoinGecko OHLC response row should be converted from provider array form into
a raw object payload with these fields:

- `coin_id`
- `vs_currency`
- `days`
- `timestamp_ms`
- `open`
- `high`
- `low`
- `close`

`observed_at` is the UTC timestamp converted from `timestamp_ms`. CoinGecko
documents the OHLC timestamp as the candle close time, so Felts treats
`observed_at` as the candle close timestamp.

Use deterministic raw identity:

```text
source_record_id = coin_id|vs_currency|timestamp_ms
```

Do not include `days` in `source_record_id`. The same candle should deduplicate
across future window changes such as `days=90` to `days=180`.

With the existing raw loader, overlapping daily rolling-window captures should
skip duplicate raw records because repeated raw record IDs conflict in
`raw.raw_record_keys`. Staging and mart models should still deduplicate by candle
grain as a second guard.

## Transform Contract

Add source definition for:

- `coingecko.raw_coins_ohlc`

Add staging model:

- `coingecko.stg_coingecko__coins_ohlc`

Staging grain is one row per:

```text
coin_id, vs_currency, observed_at
```

Add mart model:

- `coingecko.mart_coingecko__coin_ohlc_candles`

The mart should keep the same candle grain as staging and expose provider-shaped
CoinGecko rows. It should not join to internal Felts mappings or filter out
unmapped rows beyond the source extraction input set.

## MCP Access Contract

Add the new mart to `settings/felts-prod-data-views.txt`:

- `coingecko.mart_coingecko__coin_ohlc_candles`

Update MCP docs and tests so schema-qualified access accepts this mart.

Production access grants remain reconciled by the existing operator command after
deployment and dbt have created the relation:

```bash
scripts/update-prod-data-access.sh
```

## Acceptance Criteria

- `coins_ohlc` is a supported CoinGecko entity.
- The extractor reads default CoinGecko IDs from the Felts provider mapping seed
  for `provider_source=coingecko`.
- The extractor requests `/coins/{coin_id}/ohlc` with `vs_currency` and `days=90`.
- The extractor rejects malformed OHLC responses.
- Extracted raw records use stable duplicate-safe identity
  `coin_id|vs_currency|timestamp_ms`.
- Daily deployment schedule for `coins_ohlc` is `0 3 * * *` UTC.
- Raw completion event payload for `coins_ohlc` includes selector
  `stg_coingecko__coins_ohlc+`.
- dbt creates the `stg_coingecko__coins_ohlc` staging model and
  `mart_coingecko__coin_ohlc_candles` mart.
- dbt tests cover not-null fields and candle-grain uniqueness.
- The MCP allowlist exposes `coingecko.mart_coingecko__coin_ohlc_candles`.
- No production access reconciliation is required for phase close-out.

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
dbt run --select stg_coingecko__coins_ohlc+
dbt test --select stg_coingecko__coins_ohlc+
```

Run focused MCP checks:

```bash
./.venv/bin/pytest tests/unit/test_prod_data_mcp.py
```

## Out of Scope Until Explicitly Approved

- Historical range backfill.
- Paid-plan interval features.
- Passing an explicit `interval` parameter.
- Market-chart capture.
- Volume capture or synthetic OHLCV.
- Broad all-CoinGecko coin OHLC sweeps.
- Canonical cross-source pricing.
- Joining the CoinGecko OHLC mart to Felts internal mappings.
- Running `scripts/update-prod-data-access.sh` against production.

# Phase 14 - CoinGecko Daily Market Metrics and OHLCV

## Goal

Add daily CoinGecko historical market metrics for mapped internal crypto assets,
derive a daily OHLCV mart by joining those metrics to daily OHLC candles, and
schedule the related CoinGecko captures.

Phase 14 also corrects the Phase 13 OHLC capture grain. Phase 13 intentionally
accepted CoinGecko's automatic OHLC granularity. For `days=90`, CoinGecko's
automatic OHLC granularity is not daily, so Phase 14 should request
`interval=daily` where daily OHLCV output is required.

## Context

- Felts is implemented through Phase 13.
- Phase 11 kept provider marts broad and modeled Felts-owned internal identity
  separately.
- Phase 12 exposed schema-qualified mart access through the controlled MCP
  production-data allowlist.
- Phase 13 added scheduled CoinGecko OHLC capture for mapped internal crypto
  assets at `03:00` UTC.
- CoinGecko already has a broad `coins_markets` extractor and
  `coingecko.mart_coingecko__coin_market_snapshots` mart.
- The existing broad market snapshot mart already exposes `current_price_usd`,
  `market_cap_usd`, and `total_volume_usd`, but those rows are current market
  snapshots, not historical daily metric rows.

## Decisions

- Keep Phase 14 focused on CoinGecko daily market metrics and derived daily
  OHLCV.
- Update CoinGecko OHLC capture to pass `interval=daily` with `days=90`.
- Add a new CoinGecko entity named `coins_market_chart`.
- Fetch `/coins/{coin_id}/market_chart` for mapped CoinGecko assets.
- Use `days=90` and `interval=daily` for market-chart requests.
- Use the existing CoinGecko `vs_currency` setting, currently
  `COINGECKO_MARKETS_VS_CURRENCY`, for both OHLC and market-chart requests.
- Default CoinGecko IDs for per-coin captures come from
  `transforms/seeds/felts/asset_provider_mappings.csv` where
  `provider_source=coingecko`.
- Read the mapping seed directly for source extraction defaults. Do not make raw
  ingestion depend on a dbt mart already existing in the warehouse.
- Treat CoinGecko `market_chart` as the volume truth for daily OHLCV.
- Do not use `/coins/markets` `total_volume` as OHLCV daily volume because it is
  a current market snapshot field.
- Keep broad `/coins/markets` provider coverage and schedule it daily. Do not
  filter the existing broad market snapshot mart to internal mappings.
- Add a derived OHLCV mart by joining daily OHLC candles to daily market-chart
  metrics.
- Expose both the standalone daily metrics mart and the derived daily OHLCV mart
  through the production MCP allowlist.
- Do not run production access reconciliation during implementation close-out.

## Provider References

- CoinGecko `/coins/{id}/ohlc` returns OHLC arrays and supports `interval=daily`
  for supported day windows such as `90`:
  <https://docs.coingecko.com/reference/coins-id-ohlc>
- CoinGecko `/coins/{id}/market_chart` returns timestamped `prices`,
  `market_caps`, and `total_volumes`, and supports `interval=daily`:
  <https://docs.coingecko.com/reference/coins-id-market-chart>
- CoinGecko `/coins/markets` returns current market data including price, market
  cap, and total volume:
  <https://docs.coingecko.com/reference/coins-markets>

## Raw Contract

Each CoinGecko market-chart response should be flattened into one raw object
payload per metric timestamp with these fields:

- `coin_id`
- `vs_currency`
- `days`
- `interval`
- `timestamp_ms`
- `price`
- `market_cap`
- `total_volume`

`observed_at` is the UTC timestamp converted from `timestamp_ms`.

Use deterministic raw identity:

```text
source_record_id = coin_id|vs_currency|interval|timestamp_ms
```

Do not include `days` in `source_record_id`. The same daily metric row should
deduplicate across future window changes such as `days=90` to `days=180`.

OHLC raw identity remains:

```text
source_record_id = coin_id|vs_currency|timestamp_ms
```

Because Phase 14 changes OHLC requests to `interval=daily`, the OHLC raw payload
should include the requested interval so downstream users can inspect the
provider request shape.

Overlapping daily 90-day captures are expected. Duplicate raw records should be
skipped by the existing raw identity path, and staging/mart models should still
deduplicate by their grain.

## Transform Contract

Add source definition for:

- `coingecko.raw_coins_market_chart`

Add staging model:

- `coingecko.stg_coingecko__coins_market_chart`

Staging grain is one row per:

```text
coin_id, vs_currency, interval, observed_at
```

Add mart model:

- `coingecko.mart_coingecko__coin_daily_market_metrics`

The daily metrics mart should keep the same daily market-chart grain and expose
provider-shaped CoinGecko rows.

Add derived mart model:

- `coingecko.mart_coingecko__coin_ohlcv_daily`

The OHLCV mart should join daily OHLC candles to daily market-chart metrics by:

```text
coin_id, vs_currency, observed_at
```

The OHLCV mart should expose:

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

The OHLCV mart is mapped-asset coverage only because both OHLC and market-chart
captures are per-coin captures driven by the internal CoinGecko mapping list.

## Scheduling

Use staggered UTC daily schedules:

- `coins_ohlc`: `0 3 * * *`
- `coins_market_chart`: `15 3 * * *`
- `coins_markets`: `30 3 * * *`

Raw completion events should trigger dbt selectors:

- `coins_ohlc`: `stg_coingecko__coins_ohlc+`
- `coins_market_chart`: `stg_coingecko__coins_market_chart+`
- `coins_markets`: `stg_coingecko__coins_markets+`

## MCP Access Contract

Add these marts to `settings/felts-prod-data-views.txt`:

- `coingecko.mart_coingecko__coin_daily_market_metrics`
- `coingecko.mart_coingecko__coin_ohlcv_daily`

Update MCP docs and tests so schema-qualified access accepts both marts.

Production access grants remain reconciled by the existing operator command
after deployment and dbt have created the relations:

```bash
scripts/update-prod-data-access.sh
```

## Acceptance Criteria

- `coins_market_chart` is a supported CoinGecko entity.
- `coins_ohlc` requests include `interval=daily`.
- `coins_market_chart` requests include `vs_currency`, `days=90`, and
  `interval=daily`.
- The market-chart extractor rejects malformed top-level or row-level provider
  shapes.
- Extracted market-chart raw records use stable duplicate-safe identity
  `coin_id|vs_currency|interval|timestamp_ms`.
- Daily deployment schedules are `03:00`, `03:15`, and `03:30` UTC for OHLC,
  market chart, and broad market snapshots respectively.
- Raw completion event payloads include selectors for `coins_ohlc`,
  `coins_market_chart`, and `coins_markets`.
- dbt creates `stg_coingecko__coins_market_chart`,
  `mart_coingecko__coin_daily_market_metrics`, and
  `mart_coingecko__coin_ohlcv_daily`.
- dbt tests cover not-null fields and model-grain uniqueness.
- The MCP allowlist exposes both new mart relations.
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
dbt run --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+
dbt test --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+
```

Run focused MCP checks:

```bash
./.venv/bin/pytest tests/unit/test_prod_data_mcp.py
```

## Out of Scope Until Explicitly Approved

- Broad all-CoinGecko per-coin OHLC or market-chart sweeps.
- Replacing the broad `/coins/markets` mart.
- Using `/coins/markets` `total_volume` as daily OHLCV volume.
- Historical range backfill.
- Intraday OHLCV.
- Canonical cross-source pricing.
- Joining the CoinGecko OHLCV mart to Felts internal mappings.
- Running `scripts/update-prod-data-access.sh` against production.

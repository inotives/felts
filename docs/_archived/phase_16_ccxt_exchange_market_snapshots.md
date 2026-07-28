# Phase 16 - CCXT Exchange Market Snapshots

## Goal

Add the first CCXT-based exchange market-data vertical slice for public ticker
and order book snapshots.

Phase 16 starts with Binance `BTC/USDT` through CCXT public APIs, lands the data
in the existing raw pipeline, exposes provider-native dbt marts, and adds those
marts to the controlled MCP production-data access surface.

## Context

- Felts is implemented through Phase 15.
- Existing source-owned marts stay provider-native unless a separate Felts-owned
  internal mapping model explicitly joins them.
- Phase 12 established the mart-first MCP access rule: expose schema-qualified
  marts only, never raw, staging, or intermediate relations.
- `ccxt` already exists in the optional `finance` dependency group, but Phase 16
  makes CCXT a first-class ingestion dependency.
- CCXT provides unified public exchange methods such as `fetch_ticker` and
  `fetch_order_book`.
- Public CCXT exchange methods do not require exchange credentials for this
  Phase 16 slice.

Provider references:

- <https://github.com/ccxt/ccxt>
- <https://github.com/ccxt/ccxt/wiki/manual>
- <https://github.com/ccxt/ccxt/blob/master/python/README.md>

## Decisions

- Move `ccxt` into the main project dependencies.
- Keep Phase 16 to one exchange and one symbol:
  - exchange: CCXT `binance`
  - symbol: `BTC/USDT`
- Require the live smoke to use CCXT `binance` exactly. If Binance public API
  access is blocked from the execution environment, record that as a blocker
  instead of silently switching to another exchange.
- Define the market universe through a committed seed/config, not hard-coded
  constants.
- Start the committed universe with Binance `BTC/USDT`.
- Capture two separate entities:
  - `ticker`
  - `order_book`
- Use `fetch_ticker("BTC/USDT")` for ticker snapshots.
- Use `fetch_order_book("BTC/USDT", limit=20)` for order book snapshots.
- Capture the top 20 order book levels.
- Keep order book downstream modeling as one snapshot row per capture, with
  top-of-book fields plus full top-20 bid and ask arrays preserved as JSON.
- Use `observed_at` as:
  - the provider timestamp when CCXT returns one;
  - the extraction timestamp when the provider timestamp is absent.
- Build duplicate identity from source, entity, exchange, symbol, and
  `observed_at`.
- If one requested entity succeeds and another fails, keep successful inserted
  records but fail the overall run and report per-entity evidence.
- Keep Phase 16 manual only. Do not add a cron or Prefect schedule for CCXT yet.
- Expose only final CCXT marts through MCP.
- Do not connect CCXT markets to Felts internal asset mappings in Phase 16.
- Do not introduce an internal exchange market or pair domain model in Phase 16.

## Source Contract

Add a source-owned CCXT package following the existing source runner and raw
writer patterns.

The committed CCXT market universe should contain at least:

- `exchange_id`
- `symbol`
- `base_asset`
- `quote_asset`
- `order_book_limit`
- `is_active`

Initial active row:

| exchange_id | symbol  | base_asset | quote_asset | order_book_limit | is_active |
|-------------|---------|------------|-------------|------------------|-----------|
| binance     | BTC/USDT | BTC        | USDT        | 20               | true      |

Ticker raw payloads should include:

- `exchange_id`
- `symbol`
- `base_asset`
- `quote_asset`
- `timestamp`
- `datetime`
- `bid`
- `ask`
- `last`
- `open`
- `high`
- `low`
- `close`
- `base_volume`
- `quote_volume`
- `vwap`
- `percentage`
- `raw_response`

Order book raw payloads should include:

- `exchange_id`
- `symbol`
- `base_asset`
- `quote_asset`
- `limit`
- `timestamp`
- `datetime`
- `nonce`
- `best_bid`
- `best_ask`
- `bids`
- `asks`
- `raw_response`

For both entities:

- `source` is `ccxt`.
- `entity` is `ticker` or `order_book`.
- `observed_at` follows the provider-timestamp-then-extraction-time rule.
- `source_record_id` is stable for one snapshot identity:

  ```text
  <entity>|<exchange_id>|<symbol>|<observed_at>
  ```

The implementation may normalize names to match existing raw table naming rules,
but the entity distinction must remain visible in raw, staging, and mart models.

## Transform Contract

Add staging models in the `ccxt` schema:

- `ccxt.stg_ccxt__tickers`
- `ccxt.stg_ccxt__order_books`

Ticker staging grain:

```text
exchange_id, symbol, observed_at
```

Order book staging grain:

```text
exchange_id, symbol, observed_at
```

Add mart models in the `ccxt` schema:

- `ccxt.mart_ccxt__tickers`
- `ccxt.mart_ccxt__order_book_snapshots`

The ticker mart remains provider-native at one row per ticker snapshot and
exposes typed fields from ticker staging.

The order book mart remains one row per snapshot and exposes:

- exchange and symbol identity
- `observed_at`
- `best_bid`
- `best_ask`
- `spread`
- `mid_price`
- top-20 `bids` JSON
- top-20 `asks` JSON
- `raw_record_id`

Do not add a flattened order book levels mart in Phase 16.

## MCP Access Contract

Add the two CCXT marts to the committed schema-qualified MCP allowlist:

- `ccxt.mart_ccxt__tickers`
- `ccxt.mart_ccxt__order_book_snapshots`

Do not allowlist:

- CCXT raw tables
- CCXT staging models
- future intermediate CCXT models

Update the MCP docs and unit tests so the allowlist remains mart-first and
schema-qualified.

## Acceptance Criteria

- `ccxt` is a main dependency, not only an optional finance dependency.
- The committed market universe seeds Binance `BTC/USDT` with order book limit
  20.
- The CCXT source can run ticker and order book capture for Binance `BTC/USDT`.
- Ticker extraction uses `fetch_ticker`.
- Order book extraction uses `fetch_order_book` with limit 20.
- Raw records are written under the `ccxt` source schema.
- `observed_at` uses provider timestamp when present and extraction time when
  absent.
- Successful entity records are preserved even if another requested entity fails.
- The overall command or flow fails when any requested entity fails.
- `stg_ccxt__tickers` and `stg_ccxt__order_books` build from raw CCXT records.
- `mart_ccxt__tickers` and `mart_ccxt__order_book_snapshots` build from staging.
- The order book mart keeps one row per snapshot and preserves top-20 bid/ask
  arrays as JSON.
- The committed MCP allowlist exposes the two CCXT marts and no CCXT raw or
  staging relations.
- No CCXT cron or scheduled deployment is added.
- No Felts internal asset mapping or internal market-pair model is added.

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
dbt run --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots
dbt test --select stg_ccxt__tickers stg_ccxt__order_books mart_ccxt__tickers mart_ccxt__order_book_snapshots
```

Run the required live smoke check:

```bash
./.venv/bin/felts ccxt run --entities ticker order_book
```

Then inspect raw, staging, mart, and MCP access evidence for Binance `BTC/USDT`.

If sandboxed dbt cannot connect to local Postgres on `localhost:5432`, rerun dbt
outside the sandbox and record that in task notes.

If Binance public API access is blocked from the execution environment, record
the exact CCXT error and treat the task as blocked until the exchange target is
changed by a follow-up decision.

## Out of Scope Until Explicitly Approved

- Scheduled CCXT capture.
- Exchange credentials or private account APIs.
- Exchange trading, balances, positions, or order placement.
- Additional exchanges beyond CCXT `binance`.
- Additional symbols beyond `BTC/USDT`.
- Flattened order book level marts.
- Order book retention or compaction policy.
- Historical order book backfill.
- OHLCV ingestion through CCXT.
- Felts internal exchange market or trading pair identity.
- Felts internal asset/provider mappings for CCXT.
- Running `scripts/update-prod-data-access.sh` against production.

---
id: task-0028
title: "Phase 16: CCXT source and market universe"
type: task
status: pending
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

Phase 16 adds the first CCXT public exchange market-data vertical slice.

Source of truth:

- `docs/phases/phase_16_ccxt_exchange_market_snapshots.md`

## Goal

Add the CCXT dependency, committed market universe, source extraction, raw load,
and CLI path for Binance `BTC/USDT` ticker and top-20 order book snapshots.

## Scope

- Move `ccxt` from the optional finance dependency group into main dependencies.
- Add a committed CCXT market universe with active Binance `BTC/USDT` and order
  book limit 20.
- Add a source-owned CCXT package following existing source runner/raw writer
  patterns.
- Add separate entities:
  - `ticker`
  - `order_book`
- Implement ticker capture with `fetch_ticker("BTC/USDT")`.
- Implement order book capture with `fetch_order_book("BTC/USDT", limit=20)`.
- Use provider timestamp for `observed_at` when available, otherwise extraction
  time.
- Build `source_record_id` as:

  ```text
  <entity>|<exchange_id>|<symbol>|<observed_at>
  ```

- Preserve successful entity records even when another requested entity fails,
  but fail the overall run if any requested entity fails.
- Register the CLI path:

  ```bash
  ./.venv/bin/felts ccxt run --entities ticker order_book
  ```

## Planner Notes

Do not add a CCXT cron, Prefect schedule, exchange credentials, private account
APIs, internal asset mapping, or internal exchange market model in this task.

The required exchange target is CCXT `binance`; do not silently switch to
`binanceus` or another exchange if access fails.

## Implementation Plan

1. Update dependencies and lock files consistently with the repo tooling.
2. Add the committed CCXT market universe seed/config.
3. Implement the CCXT extractor/client using public CCXT methods only.
4. Implement the CCXT runner and raw payload construction for both entities.
5. Register the CCXT CLI command.
6. Add focused unit tests for dependency-visible imports, market universe loading,
   entity extraction shape, timestamp fallback, source record IDs, and partial
   failure behavior.
7. Run focused unit tests and record results in `## Notes`.

## Acceptance Criteria

- [ ] `ccxt` is a main dependency, not only an optional finance dependency.
- [ ] The committed market universe includes active Binance `BTC/USDT` with
      order book limit 20.
- [ ] Ticker extraction uses `fetch_ticker`.
- [ ] Order book extraction uses `fetch_order_book` with limit 20.
- [ ] Raw records are written with source `ccxt`.
- [ ] Entities remain distinct as `ticker` and `order_book`.
- [ ] `observed_at` uses provider timestamp when present and extraction time
      when absent.
- [ ] `source_record_id` follows
      `<entity>|<exchange_id>|<symbol>|<observed_at>`.
- [ ] Successful entity rows are preserved if another requested entity fails.
- [ ] The overall command or runner result fails when any requested entity fails.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes

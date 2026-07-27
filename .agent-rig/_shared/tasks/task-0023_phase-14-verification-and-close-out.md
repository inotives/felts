---
id: task-0023
title: "Phase 14: verification and close-out"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-27
updated_on: 2026-07-27
priority: normal
parent: ""
depends_on:
  - task-0022
---





# Task

## Context

Tasks 0020 through 0022 implement Phase 14 CoinGecko daily market metrics,
derived OHLCV, scheduling, and MCP exposure.

Source of truth:

- `docs/phases/phase_14_coingecko_daily_market_metrics_and_ohlcv.md`

## Goal

Run final local verification for Phase 14 and update implemented-state docs.

## Scope

- Run fast checks:
  - `./.venv/bin/ruff check .`
  - `./.venv/bin/ruff format --check .`
  - `./.venv/bin/python -m mypy`
  - `./.venv/bin/pytest tests/unit`
- Run focused CoinGecko and MCP tests.
- Run dbt checks:
  - `dbt seed`
  - `dbt run --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
  - `dbt test --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
- Update implemented-state docs after checks pass.
- Record exact command evidence in `## Notes`.
- Do not run `scripts/update-prod-data-access.sh` against production.
- Do not archive the Phase 14 doc unless the human explicitly asks after merge.

## Planner Notes

Production access reconciliation remains an operator step after deployment and dbt
have created the Phase 14 marts in production.

## Implementation Plan

1. Confirm task dependencies are complete.
2. Run focused unit tests for CoinGecko market chart, OHLC daily interval,
   schedules, event selectors, and MCP access.
3. Run full fast checks.
4. Run focused dbt checks.
5. Update README/project specs/current docs to say Felts is implemented through
   Phase 14 and includes daily CoinGecko market metrics plus derived OHLCV.
6. Record exact command outcomes in this task.

## Acceptance Criteria

- [ ] Focused CoinGecko source tests pass.
- [ ] Focused MCP tests pass.
- [ ] Fast local checks pass.
- [ ] Focused dbt checks pass or an environment blocker is documented.
- [ ] Implemented-state docs describe Phase 14.
- [ ] Task notes contain exact verification commands and results.
- [ ] No production reconciliation command is run.

## Notes

- Updated implemented-state docs in `README.md` and `docs/project_specs.md`.
- Final implemented-state wording now remains at Phase 13, with Phase 14
  described as in progress pending a live OHLC ingest fix.
- No production reconciliation command was run.
- Verification:
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
    -> `31 passed in 1.33s`
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
    -> `37 passed in 0.31s`
  - `./.venv/bin/ruff check .`
    -> `All checks passed!`
  - `./.venv/bin/ruff format --check .`
    -> `103 files already formatted`
  - `./.venv/bin/python -m mypy`
    -> `Success: no issues found in 91 source files`
  - `./.venv/bin/pytest tests/unit`
    -> `134 passed in 1.61s`
  - `./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
    -> `PASS=3 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=3`
  - `./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    -> `PASS=5 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=5`
  - `./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    -> `PASS=45 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=45`

### Reviewer Notes

- Returned to `ready` on Monday, July 27, 2026.
- Local close-out checks passed during review:
  - `./.venv/bin/pytest tests/unit/sources/coingecko/test_extractor.py tests/unit/sources/coingecko/test_runner.py tests/unit/sources/coingecko/test_deployments.py tests/unit/sources/coingecko/test_events.py -q`
    -> `31 passed in 2.07s`
  - `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q`
    -> `37 passed in 0.43s`
  - `./.venv/bin/ruff check .`
    -> `All checks passed!`
  - `./.venv/bin/ruff format --check .`
    -> `103 files already formatted`
  - `./.venv/bin/python -m mypy`
    -> `Success: no issues found in 91 source files`
  - `./.venv/bin/pytest tests/unit -q`
    -> `134 passed in 1.47s`
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms`
    -> `PASS=3 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=3`
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    -> `PASS=5 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=5`
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select stg_coingecko__coins_ohlc+ stg_coingecko__coins_market_chart+`
    -> `PASS=45 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=45`
- Blocking live repro:
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/felts coingecko run --entities coins_ohlc`
    -> failed with `felts.core.exceptions.ExtractionError`
    -> root cause from provider response: `400 Bad Request` for `https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=90&interval=daily`
  - `env UV_CACHE_DIR=/tmp/felts-uv-cache ./.venv/bin/felts coingecko run --entities coins_market_chart`
    -> `source=coingecko entity=coins_market_chart extracted=270 inserted=3 skipped_duplicate=267 invalid=0 failed=0`
- Review conclusion:
  - `README.md` and `docs/project_specs.md` currently say Felts is implemented through Phase 14, but the live Phase 14 OHLC ingest path is still broken.
  - Fix the live `coins_ohlc` request shape or reduce the implemented-state wording so it does not claim full Phase 14 implementation while the upstream OHLC path fails live.

### Follow-up Fix

- Updated `README.md` and `docs/project_specs.md` on Monday, July 27, 2026 to
  restore implemented-state wording to Phase 13 and to describe Phase 14 as
  in progress pending a live OHLC ingest fix.
- The Phase 14 local verification evidence above remains valid; this follow-up
  only corrects the top-level implemented-state claim to match the reviewer’s
  live repro.

### OHLC Failure Root Cause

- Investigated on Monday, July 27, 2026 against the live public CoinGecko API.
- Exact provider error body for the failing request:
  - `https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=90&interval=daily`
  - status `400`
  - body `{"error":"invalid interval parameter"}`
- Comparison repros:
  - `https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=90`
    -> status `200`
  - `https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=90&interval=hourly`
    -> status `400`
- Likely root cause:
  - CoinGecko's current OHLC docs say `interval=daily` and `interval=hourly`
    on `/coins/{id}/ohlc` are paid-plan subscriber features.
  - Felts is currently calling the public `api.coingecko.com` endpoint without
    a paid-plan key, so the public API rejects the explicit `interval`
    override even though the same endpoint works with `days=90` when `interval`
    is omitted.
- Worker follow-up direction:
  - Either switch OHLC extraction to a CoinGecko paid-plan base URL/key that
    supports `interval=daily`, or change the implementation/docs so Felts does
    not rely on `/coins/{id}/ohlc?interval=daily` on the public API.
  - If staying on the public API, Phase 14 daily OHLCV should likely be driven
    from `market_chart` daily metrics plus a different OHLC strategy, because
    public `/coins/{id}/ohlc` currently returns only auto-granularity candles
    for `days=90`.

### Public API Fallback Direction

- Confirmed on Monday, July 27, 2026 that public `/coins/{id}/ohlc` without an
  explicit `interval` works, but does **not** return daily candles for
  `days=90`.
- Live public API check:
  - `https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=90`
    -> status `200`
    -> returned `23` rows
    -> first timestamps:
      - `2026-04-29T00:00:00+00:00`
      - `2026-05-03T00:00:00+00:00`
      - `2026-05-07T00:00:00+00:00`
    -> observed spacing `96` hours, so provider output is `4` day candles
- CoinGecko docs match the live result for `/coins/{id}/ohlc` auto-granularity:
  - `1-2` days -> `30` minute candles
  - `3-30` days -> `4` hour candles
  - `31+` days -> `4` day candles
- Proposed worker fix direction if Felts stays on the public API:
  - Change OHLC extraction to `days=30` and remove the `interval` parameter.
  - Accept provider `4` hour OHLC candles as the raw source.
  - Derive daily OHLC in staging from the `4` hour candles by UTC date:
    - `open` = first candle open of the UTC day
    - `high` = max high of the UTC day
    - `low` = min low of the UTC day
    - `close` = last candle close of the UTC day
  - Update the raw/staging/docs contract so Felts no longer claims the provider
    returned direct daily OHLC candles. Under this fallback, daily OHLC becomes
    a Felts-derived rollup from provider `4` hour candles.

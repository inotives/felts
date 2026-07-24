---
id: task-0012
title: "Phase 11: dbt verification and docs close-out"
type: task
status: done
assigned_to: worker
created_by: human
created_on: 2026-07-24
updated_on: 2026-07-24
priority: normal
parent: ""
depends_on:
  - task-0011
---










# Task

## Context

Tasks 0009 through 0011 implement the Phase 11 internal mapping marts and
source-owned mart completion. This task proves the full dbt path and updates docs
for close-out.

Source of truth:

- `docs/phases/phase_11_analytical_marts_and_internal_assets.md`

## Goal

Run final Phase 11 verification and update docs to reflect the implemented mart and
internal asset mapping surface.

## Scope

- Run fast checks:
  - `make lint`
  - `make format-check`
  - `make typecheck`
  - `make test`
- Run DB-backed dbt checks:
  - `make dbt-debug`
  - `uv run dbt seed --project-dir transforms --profiles-dir transforms`
  - `uv run dbt run --project-dir transforms --profiles-dir transforms --select marts`
  - `uv run dbt test --project-dir transforms --profiles-dir transforms --select marts`
- Update implemented-state docs after checks pass.
- Record exact command evidence in `## Notes`.
- Do not mark Phase 11 implemented if DB-backed dbt verification is skipped.
- Do not move the Phase 11 phase doc to `docs/_archived/` in this task unless the
  human explicitly asks for archive close-out after merge.

## Planner Notes

The key close-out evidence is dbt seed/run/test against local Postgres. Static file
checks alone are not enough for this phase.

## Implementation Plan

1. Confirm task dependencies are done or ready for review.
2. Run fast checks.
3. Run dbt seed, mart run, and mart tests against local Postgres.
4. Update docs that describe implemented mart/internal mapping state.
5. Record exact commands and outcomes in this task's notes.

## Acceptance Criteria

- [ ] Fast checks pass.
- [ ] `make dbt-debug` passes.
- [ ] `dbt seed` passes.
- [ ] `dbt run --select marts` passes.
- [ ] `dbt test --select marts` passes.
- [ ] Docs describe Phase 11's implemented source-owned marts and `felts` internal
  mapping marts.
- [ ] Task notes contain exact verification commands and results.
- [ ] Phase 11 is not marked implemented without DB-backed dbt evidence.

## Notes
- Verification on 2026-07-24:
  - `make lint` succeeded.
  - `make format-check` succeeded.
  - `make typecheck` succeeded.
  - `make test` succeeded with `98 passed`.
  - `make dbt-debug` succeeded outside the sandbox after starting local Docker Postgres.
  - One-time local ingestion to create missing raw tables succeeded:
    - `.venv/bin/felts coingecko run --entities asset_platforms_list global global_defi coins_markets`
    - `.venv/bin/felts csv import --contract ohlcv --input-uri data/ohlcv/crypto-ohlcv-bitcoin-20260621.csv`
    - `.venv/bin/felts csv import --contract fred_series --input-uri data/fred/us_cpi-202605.csv`
  - `.venv/bin/dbt seed --project-dir transforms --profiles-dir transforms` succeeded: `PASS=3`.
  - `.venv/bin/dbt run --project-dir transforms --profiles-dir transforms --select marts` succeeded: `PASS=11`.
  - `.venv/bin/dbt test --project-dir transforms --profiles-dir transforms --select marts` succeeded: `PASS=35`.
  - Implemented-state docs updated in `README.md`, `docs/project_specs.md`, and this
    Phase 11 doc.
- Reviewer return on 2026-07-24:
  - `docs/phases/phase_11_analytical_marts_and_internal_assets.md` still says the
    CoinGecko market/global/DeFi staging models do not yet have marts and still says
    Alpha Vantage and CSV import have staging models but no marts. Update those
    context lines so the phase doc matches the implemented Phase 11 state.
  - `README.md` still has a stale `## dbt` implemented-transforms section that only
    lists CoinGecko staging, CoinGecko coins/asset-platform marts, and CSV staging.
    Expand it so the README matches the Phase 11 implemented mart surface.
  - `docs/project_specs.md` still says `Last Updated: 2026-07-19` even though this
    close-out updates implemented-state docs on 2026-07-24. Refresh the metadata so
    the spec is internally consistent with the claimed doc update.

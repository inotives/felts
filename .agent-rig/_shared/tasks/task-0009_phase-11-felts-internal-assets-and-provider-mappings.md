---
id: task-0009
title: "Phase 11: Felts internal assets and provider mappings"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-24
updated_on: 2026-07-24
priority: normal
parent: ""
depends_on: []
---



# Task

## Context

Phase 11 adds a Felts-owned internal asset mapping layer while keeping provider
marts broad.

Source of truth:

- `docs/phases/phase_11_analytical_marts_and_internal_assets.md`

## Goal

Add the minimal curated dbt seed and mart contract for Felts internal assets,
asset platforms, and provider mappings.

## Scope

- Configure dbt so Felts-owned marts materialize in schema `felts`.
- Configure dbt seeds in the smallest stable way needed by the new internal marts.
- Add curated seeds for:
  - internal assets;
  - internal asset platforms;
  - asset provider mappings.
- Add Felts internal mart models:
  - `felts.mart_felts__assets`
  - `felts.mart_felts__asset_platforms`
  - `felts.mart_felts__asset_provider_mappings`
- Seed these initial internal assets:
  - `bitcoin` (`crypto`, symbol `BTC`)
  - `ethereum` (`crypto`, symbol `ETH`)
  - `solana` (`crypto`, symbol `SOL`)
  - `apple` (`stock`, symbol `AAPL`)
  - `taiwan-semiconductor` (`stock`, symbol `TSM`)
  - `nvidia` (`stock`, symbol `NVDA`)
  - `spcx` (`stock`, symbol `SPCX`)
  - `usd` (`currency`, symbol `USD`)
- Seed these initial internal asset platforms:
  - `ethereum`
  - `solana`
- Add provider mappings for CoinGecko crypto IDs and Alpha Vantage stock symbols.
- Do not infer mappings from provider data.
- Do not filter or modify provider marts in this task.

## Planner Notes

Keep this seed-backed and boring. Do not add a mapping service, automatic matching,
or bridge-table hierarchy beyond the one provider-mapping mart required by the phase
doc.

## Implementation Plan

1. Add seed CSV files under `transforms/seeds/`.
2. Add dbt config for the seeds and `marts/felts`.
3. Add Felts mart SQL models that select from the curated seeds.
4. Add model YAML descriptions and tests for uniqueness and not-null keys.
5. Run focused dbt seed/test commands if local Postgres is available; otherwise run
   the closest static checks and record the missing prerequisite.

## Acceptance Criteria

- [ ] `mart_felts__assets` exposes one row per curated internal asset.
- [ ] `mart_felts__asset_platforms` exposes one row per curated internal platform.
- [ ] `mart_felts__asset_provider_mappings` maps internal assets to CoinGecko and
  Alpha Vantage provider identifiers.
- [ ] Internal asset IDs are unique and not null.
- [ ] Internal asset platform IDs are unique and not null.
- [ ] Provider mapping keys are unique for each provider source and provider asset
  identifier.
- [ ] Internal IDs use readable lowercase slugs and do not rename any existing IDs.
- [ ] No provider mart filters are introduced in this task.
- [ ] Focused verification results are recorded in `## Notes`.

## Notes


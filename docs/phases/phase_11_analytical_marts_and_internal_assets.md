# Phase 11 - Analytical Marts and Felts Internal Assets

## Goal

Complete consumer-facing mart coverage for sources that already have stable staging
models, and add a separate Felts-owned internal asset mapping layer.

Phase 11 keeps provider marts broad. CoinGecko marts should continue to expose all
available CoinGecko rows. Internal identity is modeled separately in the `felts`
schema so consumers can opt into Felts-owned asset and platform identifiers when
they need cross-provider joins.

## Context

- Felts is implemented through Phase 10.
- CoinGecko currently has reference marts for coins and asset platforms.
- CoinGecko staging also contains market, global, and DeFi snapshots that do not yet
  have marts.
- Alpha Vantage and CSV import have staging models but no mart models.
- Agent-pipe stops at raw landing and has no stable staging or mart contract yet.
- The existing dbt schema macro honors explicit `+schema` config, so a `felts`
  mart schema can be added through dbt project configuration.

## Decisions

- Scope is marts plus curated internal mapping seeds only.
- Keep all CoinGecko data in CoinGecko marts; do not filter CoinGecko marts to
  internally mapped assets.
- Add a new `felts` schema for Felts-owned internal assets, internal asset
  platforms, and provider mappings.
- Internal mappings are manually curated seeds, not inferred from provider data.
- Provider marts remain provider-native. Consumers join provider marts to `felts`
  marts when they need internal identity.
- Internal assets have an `asset_type` such as `crypto`, `stock`, or `currency`.
- Internal IDs are readable lowercase slugs.
- If a proposed internal ID collides with an existing slug, append the shortest
  stable disambiguating suffix needed.
- Do not rename existing internal IDs just because a later collision appears.
- Initial internal assets are:
  - `bitcoin` (`crypto`, symbol `BTC`)
  - `ethereum` (`crypto`, symbol `ETH`)
  - `solana` (`crypto`, symbol `SOL`)
  - `apple` (`stock`, symbol `AAPL`)
  - `taiwan-semiconductor` (`stock`, symbol `TSM`)
  - `nvidia` (`stock`, symbol `NVDA`)
  - `spcx` (`stock`, symbol `SPCX`)
  - `usd` (`currency`, symbol `USD`)
- Initial internal asset platforms are:
  - `ethereum`
  - `solana`
- No ADR is required unless implementation uncovers a harder-to-reverse mapping
  decision than the seed-backed contract above.

## dbt Models

### Source-owned marts

Existing broad CoinGecko marts remain:

- `coingecko.mart_coingecko__coins`
- `coingecko.mart_coingecko__asset_platforms`

Add missing broad CoinGecko marts:

- `coingecko.mart_coingecko__coin_market_snapshots`
- `coingecko.mart_coingecko__global_market_snapshots`
- `coingecko.mart_coingecko__global_defi_snapshots`

Add missing Alpha Vantage and CSV marts:

- `alphavantage.mart_alphavantage__daily_prices`
- `csv_import.mart_csv_import__ohlcv`
- `csv_import.mart_csv_import__fred_observations`

Each source-owned mart should select from its matching staging model, preserve the
staging model grain, expose typed consumer columns, and keep useful lineage fields
already present in staging.

### Felts internal marts

Add Felts-owned marts:

- `felts.mart_felts__assets`
- `felts.mart_felts__asset_platforms`
- `felts.mart_felts__asset_provider_mappings`

The internal asset provider mapping mart links Felts internal assets to provider
identifiers from CoinGecko and Alpha Vantage. CoinGecko and Alpha Vantage mart rows
should not be dropped when no internal mapping exists.

## Seed Contract

Add curated dbt seeds for:

- Internal assets.
- Internal asset platforms.
- Asset provider mappings.

Minimum seed fields:

- Internal assets: internal asset ID, display name, symbol, asset type.
- Internal asset platforms: internal asset platform ID, display name.
- Provider mappings: internal asset ID, provider source, provider asset identifier.

Provider mapping examples:

- CoinGecko crypto mappings use CoinGecko coin IDs such as `bitcoin`, `ethereum`,
  and `solana`.
- Alpha Vantage stock mappings use symbols such as `AAPL`, `TSM`, `NVDA`, and
  `SPCX`.

## Acceptance Criteria

- Phase 11 planning docs are committed to `main` before implementation starts on a
  feature branch.
- dbt config materializes source-owned marts into their source schemas and Felts
  internal marts into the `felts` schema.
- CoinGecko mart coverage remains broad and is not limited to internal mappings.
- Felts internal marts expose the curated internal asset/platform list and provider
  mappings.
- New model YAML documents each new mart and tests its declared grain.
- Internal asset IDs and internal asset platform IDs are unique and not null.
- Provider mapping keys are unique for each provider source and provider asset
  identifier.
- The implementation records dbt seed, run, and test evidence in task notes or PR
  notes.

## Verification

Run fast checks:

```bash
make lint
make format-check
make typecheck
make test
```

Run DB-backed dbt checks:

```bash
make dbt-debug
uv run dbt seed --project-dir transforms --profiles-dir transforms
uv run dbt run --project-dir transforms --profiles-dir transforms --select marts
uv run dbt test --project-dir transforms --profiles-dir transforms --select marts
```

## Out of Scope Until Explicitly Approved

- New extractors or source entities.
- Agent-pipe staging or marts.
- Derived metrics such as returns, moving averages, or signals.
- A canonical cross-source price mart.
- A dashboard, UI, query app, or MCP change.
- Automatic internal asset inference from provider data.
- Dropping unmapped provider rows from source-owned marts.
- Renaming existing internal IDs after they have been published.

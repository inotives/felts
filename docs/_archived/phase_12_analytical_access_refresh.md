# Phase 12 - Analytical Access Refresh

## Goal

Refresh the controlled production analytical access layer so agents and operators can
query the Phase 11 mart surface through the existing Felts MCP path.

Phase 12 does not add new analytics. It makes the mart layer that already exists
available through the schema-qualified allowlist, tests, docs, and safe access-grant
script path.

## Context

- Felts is implemented through Phase 11.
- Phase 11 added source-owned marts for CoinGecko, Alpha Vantage, CSV import, and
  Felts-owned internal asset mapping marts.
- `settings/felts-prod-data-views.txt` is the single source of truth for MCP query
  policy and production access grants.
- The current allowlist still includes staging relations where Phase 11 now provides
  consumer-facing mart replacements.
- `scripts/update-prod-data-access.sh` is the safe rerunnable operator command for
  reconciling the `felts_ai` production access role with the committed allowlist.

## Decisions

- Scope is access refresh only.
- Do not add reports, dashboards, a query app, new marts, or new ingestion.
- Prefer marts over staging where a mart replacement exists.
- Keep schema-qualified allowlist entries. MCP clients must query exact
  `schema.relation` names.
- Update the allowlist to expose the Phase 11 consumer-facing mart surface.
- Remove staging allowlist entries where a mart now replaces them.
- Keep the existing SQL safety policy unless tests expose a current bug.
- Verification requires local and script proof only.
- Do not require live production access reconciliation as phase close-out.
- Production reconciliation remains an operator step after deployment and dbt have
  created the Phase 11 relations in production.

## Allowlist Contract

Phase 12 should allowlist these mart relations:

- `coingecko.mart_coingecko__asset_platforms`
- `coingecko.mart_coingecko__coins`
- `coingecko.mart_coingecko__coin_market_snapshots`
- `coingecko.mart_coingecko__global_market_snapshots`
- `coingecko.mart_coingecko__global_defi_snapshots`
- `alphavantage.mart_alphavantage__daily_prices`
- `csv_import.mart_csv_import__ohlcv`
- `csv_import.mart_csv_import__fred_observations`
- `felts.mart_felts__assets`
- `felts.mart_felts__asset_platforms`
- `felts.mart_felts__asset_provider_mappings`

Phase 12 should remove staging entries that now have mart replacements, including:

- `public.stg_alphavantage__time_series_daily`
- `coingecko.stg_coingecko__asset_platforms_list`
- `coingecko.stg_coingecko__coins_list`
- `coingecko.stg_coingecko__coins_markets`
- `coingecko.stg_coingecko__global`
- `coingecko.stg_coingecko__global_defi`
- `csv_import.stg_csv_import__fred_series`
- `csv_import.stg_csv_import__ohlcv`

If implementation discovers a staging relation without a mart replacement, keep it
only with an explicit note in this phase doc or task notes.

## Acceptance Criteria

- The committed allowlist exposes the Phase 11 marts listed above.
- The committed allowlist no longer exposes staging relations that have mart
  replacements.
- MCP documentation describes the mart-first access contract and keeps the safe
  production reconciliation command.
- Unit tests cover:
  - committed allowlist contents;
  - `validate_query` accepting the new schema-qualified mart names;
  - `describe_allowed_view` for non-`coingecko` schemas such as `felts`,
    `alphavantage`, and `csv_import`;
  - rejection of removed staging relations.
- The access-grant script still validates schema-qualified allowlist entries.
- No live production reconciliation is required for phase close-out.

## Verification

Run fast checks:

```bash
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/python -m mypy
./.venv/bin/pytest tests/unit
```

Run focused MCP tests:

```bash
./.venv/bin/pytest tests/unit/test_prod_data_mcp.py
```

Run a local script syntax check:

```bash
bash -n scripts/update-prod-data-access.sh
```

## Out of Scope Until Explicitly Approved

- Running `scripts/update-prod-data-access.sh` against production.
- Adding saved analytical reports or example-query command surfaces.
- Adding Grafana or another visualization application.
- Adding new data sources or new mart models.
- Changing the MCP SQL safety policy without a concrete bug.
- Exposing raw tables through MCP.

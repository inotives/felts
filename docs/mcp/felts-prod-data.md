# felts-prod-data MCP

`felts-prod-data` exposes allowlisted Felts production analytical views to MCP
clients through `scripts/felts-prod-data-mcp`.

The committed allowlist in `settings/felts-prod-data-views.txt` is schema-qualified and
is the single source of truth for both MCP query policy and the rerunnable access-grant
script. Queries must reference allowlisted views by exact `schema.view` name.
Phase 12 makes that allowlist mart-first: when a consumer-facing mart exists, MCP
clients should use the mart relation instead of an older staging relation.

Preferred access is the committed mart surface:

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

## Local setup

1. Copy the local environment template:

   ```bash
   cp settings/.env.mcp.example settings/.env.mcp.local
   ```

2. Fill `FELTS_MCP_DB_PASSWORD` with the production `felts_ai` password from
   `settings/.env.prod` on the production Linux machine.

3. Ensure SSH key or agent access works without a password prompt:

   ```bash
   ssh inotives@192.168.50.182 true
   ```

## Codex registration

Register globally with:

```bash
codex mcp add felts-prod-data -- /Users/inotives/workspaces/felts/scripts/felts-prod-data-mcp
```

Verify with:

```bash
codex mcp get felts-prod-data
```

## OpenCode registration

OpenCode exposes MCP registration through:

```bash
opencode mcp add felts-prod-data
```

When prompted for a local server command, use:

```bash
/Users/inotives/workspaces/felts/scripts/felts-prod-data-mcp
```

Verify with:

```bash
opencode mcp list
```

## Production access operations

Production scripts must not drop, truncate, delete, or update production data. If
`settings/.env.prod` already exists, deployment must refuse to continue when the expected
Docker volume, roles, or databases are missing.

Host bootstrap is rare and should not be used for routine MCP access updates:

```bash
scripts/deploy-linux-mint.sh
```

Safe MCP data-access reconciliation is rerunnable after dbt creates new allowlisted views:

```bash
scripts/update-prod-data-access.sh
```

That command reconciles the production `felts_ai` role to the committed
`settings/felts-prod-data-views.txt` allowlist. Keep the file and the granted access
in sync through the script instead of editing grants manually.

Rotate the `felts_ai` password explicitly:

```bash
scripts/update-prod-data-access.sh --rotate-ai-password
```

Disable or re-enable agent database login:

```bash
scripts/manage-prod-data-access.sh disable
scripts/manage-prod-data-access.sh enable
```

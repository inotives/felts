# Handoff: Phase 09 production data MCP

## Current state

- Local repo is on `main` at merge commit `5bab7bd`.
- Working tree was clean after pulling PR #10.
- Phase 09 docs were committed earlier:
  - `docs/phases/phase_09_production_data_agent_access.md`
  - `docs/adr/0005-felts-owned-production-data-mcp.md`
  - `docs/mcp/felts-prod-data.md`
- Phase 09 MCP implementation was merged in PR #8:
  - `src/felts/prod_data_mcp.py`
  - `scripts/felts-prod-data-mcp`
  - `settings/.env.mcp.example`
  - `settings/felts-prod-data-views.txt`
  - `tests/unit/test_prod_data_mcp.py`
- Production deploy safety hotfixes were merged:
  - PR #9 guarded deployment against missing production volume/bootstrap.
  - PR #10 split safe MCP access reconciliation into `scripts/update-prod-data-access.sh`.

## Important production rule

The user explicitly set the golden rule:

> Do not delete, update, or otherwise mutate production data in scripts we write.

Interpretation for future work:

- Never add `DROP`, `TRUNCATE`, `DELETE`, or data-changing `UPDATE` to production scripts.
- Keep host/bootstrap actions separate from safe rerunnable access reconciliation.
- `scripts/deploy-linux-mint.sh` should be rare/bootstrap only.
- `scripts/update-prod-data-access.sh` should remain the safe rerunnable MCP access script.

## What happened on prod

- Earlier deploy reruns exposed that the production Postgres data looked empty/fresh.
- User accepted that production data can be re-ingested.
- A clean reset/redeploy was performed on prod by the user.
- User re-ingested Alpha Vantage data and saved the generated `FELTS_AI_PASSWORD` locally in:
  - `settings/.env.mcp.local`
- Do not print or commit that password. It was pasted once in chat and should be treated as exposed if long-term secrecy matters.

## MCP live verification performed

From the Mac:

- SSH tunnel to `inotives@192.168.50.182` worked.
- `python3 -m uv run --group mcp --env-file settings/.env.mcp.local python -m felts.prod_data_mcp --check-db` passed.
- MCP query path using `felts_ai` worked for Alpha Vantage:
  - `select count(*) as row_count from stg_alphavantage__time_series_daily`
  - returned `row_count = 100`
- Unsafe query validation passed:
  - raw table query rejected
  - mutation rejected
  - non-aggregate no-`LIMIT` rejected
  - non-allowlisted function rejected

## Current blocker

MCP currently assumes allowlisted views are in `public`.

Actual prod state during verification:

```text
public.stg_alphavantage__time_series_daily VIEW
```

Only the Alpha Vantage allowlisted object existed where MCP could see it.

Earlier dbt output showed CoinGecko dbt models are created in the `coingecko` schema, not `public`, for example:

```text
coingecko.stg_coingecko__coins_list
coingecko.stg_coingecko__asset_platforms_list
coingecko.stg_coingecko__global
coingecko.stg_coingecko__global_defi
```

Because of that:

- `describe_view("mart_coingecko__coins")` returned zero columns.
- MCP needs to support schema-qualified allowlisted views.

## Recommended next work

Patch MCP allowlisting to be schema-qualified.

Suggested shape:

- Change `settings/felts-prod-data-views.txt` from bare names to schema-qualified names:
  - `public.stg_alphavantage__time_series_daily`
  - `coingecko.stg_coingecko__coins_list`
  - `coingecko.stg_coingecko__asset_platforms_list`
  - `coingecko.stg_coingecko__global`
  - `coingecko.stg_coingecko__global_defi`
  - `coingecko.stg_coingecko__coins_markets`
  - `coingecko.mart_coingecko__coins`
  - `coingecko.mart_coingecko__asset_platforms`
  - `csv_import.stg_csv_import__fred_series`
  - `csv_import.stg_csv_import__ohlcv`
- Update SQL validation:
  - accept schema-qualified references only when exactly allowlisted;
  - decide whether bare references are rejected or normalized only for unambiguous allowlist entries.
- Update `describe_allowed_view`:
  - split `schema.view`;
  - query `information_schema.columns` using both schema and table.
- Update `update-prod-data-access.sh`:
  - grant `USAGE` on all allowlisted schemas;
  - grant `SELECT` on each schema-qualified allowlisted relation if it exists.
- Update tests for:
  - schema-qualified allowlist loading;
  - SQL validation across `public`, `coingecko`, and `csv_import`;
  - rejection of same bare table name outside allowlist;
  - grant script does not contain destructive data statements.

## Useful commands

Local verification:

```bash
python3 -m uv run --group mcp pytest tests/unit/test_prod_data_mcp.py tests/unit/test_deploy_script_guards.py
python3 -m uv run --group mcp ruff check src tests
python3 -m uv run --group mcp mypy src/felts tests
bash -n scripts/deploy-linux-mint.sh scripts/update-prod-data-access.sh scripts/manage-prod-data-access.sh scripts/felts-prod-data-mcp
```

Prod after dbt creates views:

```bash
scripts/update-prod-data-access.sh
```

Mac MCP DB check:

```bash
python3 -m uv run --group mcp --env-file settings/.env.mcp.local python -m felts.prod_data_mcp --check-db
```

## Suggested skills

- `grill-with-docs` if the next session changes Phase 09 scope or records a new decision.
- `diagnosing-bugs` if prod deploy/MCP verification fails again.
- `ponytail` should stay active: keep the schema-qualified patch small and boring.
- `context-mode` for test output, Docker output, and any large command output.


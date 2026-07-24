---
agent: worker
role: worker
tool: codex
task: task-0010
task_title: Phase 11: broad CoinGecko mart completion
status: handoff
---

Implemented the scoped CoinGecko mart completion slice.

- Added:
  - `mart_coingecko__coin_market_snapshots`
  - `mart_coingecko__global_market_snapshots`
  - `mart_coingecko__global_defi_snapshots`
- Each mart is a direct select from its matching staging model.
- Extended the existing CoinGecko model YAML with descriptions and grain tests.

Verification on 2026-07-23:

- `dbt parse` succeeded with `UV_CACHE_DIR=/tmp/felts-uv-cache`.
- Focused `dbt run` and `dbt test` both stopped at sandboxed Postgres connection attempts to `localhost:5432` with `Operation not permitted`.

Risk:

- None beyond the existing local DB access ceiling. The marts intentionally do not join to the `felts` schema and do not filter CoinGecko rows.

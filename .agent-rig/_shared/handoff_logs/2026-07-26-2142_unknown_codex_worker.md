---
agent: worker
role: worker
tool: codex
task: task-0018
task_title: "Phase 13: OHLC MCP access and docs"
status: handoff
---

# Summary

Updated the Phase 13 MCP access surface for the new CoinGecko OHLC mart.

What changed:

- added `coingecko.mart_coingecko__coin_ohlc_candles` to
  `settings/felts-prod-data-views.txt`
- updated `tests/unit/test_prod_data_mcp.py` so:
  - the committed allowlist assertion includes the OHLC mart
  - bounded selects from the OHLC mart are accepted
  - schema-qualified describe coverage includes the OHLC mart
- updated `docs/mcp/felts-prod-data.md` to list the OHLC mart in the preferred
  mart-first MCP surface

# Verification

- `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q` -> `32 passed in 0.20s`
- `./.venv/bin/ruff check tests/unit/test_prod_data_mcp.py` -> `All checks passed!`
- `./.venv/bin/ruff format --check tests/unit/test_prod_data_mcp.py` -> `1 file already formatted`

# Notes

- No production reconciliation command was run.

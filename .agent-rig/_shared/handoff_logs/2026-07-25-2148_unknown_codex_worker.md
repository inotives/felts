---
agent: worker
role: worker
tool: codex
task: task-0014
task_title: "Phase 12: MCP tests and docs"
status: handoff
---

# Summary

Updated the Phase 12 MCP contract coverage in `tests/unit/test_prod_data_mcp.py`:

- asserted the committed allowlist matches the mart-first Phase 12 surface
- added accepted `validate_query` cases for new `alphavantage`, `csv_import`, and
  `felts` mart relations
- added rejected `validate_query` cases for removed staging relations
- broadened `describe_allowed_view` checks to non-`coingecko` schemas

Updated `docs/mcp/felts-prod-data.md` to state that MCP access is mart-first, clients
must use exact schema-qualified relation names, and production reconciliation stays on
`scripts/update-prod-data-access.sh`.

# Verification

- `./.venv/bin/pytest tests/unit/test_prod_data_mcp.py -q` -> `30 passed in 0.22s`

# Notes

- No report examples or query command surface were added.

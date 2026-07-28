---
agent: worker
role: worker
tool: codex
task: task-0028
task_title: "Phase 16: CCXT source and market universe"
status: handoff
---

# Summary

Implemented the first Phase 16 CCXT source slice and moved `task-0028` to
worker-ready review state.

# What Changed

- Moved `ccxt` from the optional `finance` group into main dependencies and
  regenerated `uv.lock`.
- Added the new `src/felts/sources/ccxt/` package:
  - `constants.py`
  - `schemas.py`
  - `extractor.py`
  - `runner.py`
  - `cli.py`
  - `__init__.py`
- Registered the top-level CLI path in `src/felts/cli.py`.
- Added the committed market-universe seed at
  `transforms/seeds/ccxt/ccxt_market_universe.csv`.
- Configured CCXT seeds in `transforms/dbt_project.yml`.
- Added focused unit coverage for:
  - market-universe loading
  - ticker and order-book extraction shape
  - provider timestamp and extraction-time fallback
  - `source_record_id` format
  - partial entity failure preservation
  - CLI exit code behavior
  - top-level CLI routing

# Verification

- `./.venv/bin/ruff check src/felts/sources/ccxt tests/unit/sources/ccxt src/felts/cli.py tests/unit/test_top_level_cli.py`
  - `All checks passed!`
- `./.venv/bin/ruff format --check src/felts/sources/ccxt tests/unit/sources/ccxt src/felts/cli.py tests/unit/test_top_level_cli.py`
  - `11 files already formatted`
- `./.venv/bin/python -m mypy src/felts/sources/ccxt src/felts/cli.py tests/unit/sources/ccxt tests/unit/test_top_level_cli.py`
  - `Success: no issues found in 11 source files`
- `./.venv/bin/pytest tests/unit/sources/ccxt/test_extractor.py tests/unit/sources/ccxt/test_runner.py tests/unit/sources/ccxt/test_cli.py tests/unit/test_top_level_cli.py -q`
  - `11 passed in 2.38s`
- `./.venv/bin/python -c 'import psycopg, sqlglot, ccxt; print("ok")'`
  - `ok`

# Notes

- I first ran plain `uv sync`, which trimmed optional groups from `.venv`; I
  corrected that with `uv sync --all-groups` before final verification.
- No live Binance smoke, dbt models, MCP allowlist changes, or scheduling work
  were added in this task.

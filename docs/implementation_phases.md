# Felts Implementation Phases

This breaks the Felts project specification into implementation phases ordered by core functionality and dependency flow. Each phase should be grilled and finalized before implementation starts.

## Phase Order

0. [Phase 00 - Project Scaffolding](./_archived/phase_00_project_scaffolding.md)
1. [Phase 01 - Core Contracts and Local Foundation](./_archived/phase_01_core_contracts.md)
2. [Phase 02 - First Source Vertical Slice](./_archived/phase_02_first_source_vertical_slice.md)
3. [Phase 03 - dbt Transform Foundation](./_archived/phase_03_dbt_transform_foundation.md)
4. [Phase 04 - Prefect Flow and Scheduling Foundation](./_archived/phase_04_prefect_orchestration.md)
5. [Phase 05 - Additional Source Patterns](./_archived/phase_05_additional_source_patterns.md)
6. [Phase 06 - Operational Hardening](./_archived/phase_06_operational_hardening.md)
7. [Phase 07 - Advanced and Deferred Capabilities](./_archived/phase_07_advanced_capabilities.md)
8. [Phase 08 - Source and Entity Scaffolding](./_archived/phase_08_source_scaffolding.md)
9. [Phase 09 - Production Data Agent Access](./_archived/phase_09_production_data_agent_access.md)
10. [Phase 10 - Agent-Pipe SQLite Raw Ingestion](./_archived/phase_10_agent_pipe_sqlite_ingestion.md)
11. [Phase 11 - Analytical Marts and Felts Internal Assets](./_archived/phase_11_analytical_marts_and_internal_assets.md)
12. [Phase 12 - Analytical Access Refresh](./_archived/phase_12_analytical_access_refresh.md)
13. [Phase 13 - CoinGecko OHLC Capture](./_archived/phase_13_coingecko_ohlc_capture.md)
14. [Phase 14 - CoinGecko Daily Market Metrics and OHLCV](./_archived/phase_14_coingecko_daily_market_metrics_and_ohlcv.md)
15. [Phase 15 - CoinGecko Public OHLC Rollup Fix](./_archived/phase_15_coingecko_public_ohlc_rollup_fix.md)
16. [Phase 16 - CCXT Exchange Market Snapshots](./_archived/phase_16_ccxt_exchange_market_snapshots.md)

## Dependency Shape

Phase 00 creates the repository and tooling skeleton. Phase 01 creates the shared contracts. Phase 02 proves one complete extract-load path. Phase 03 turns raw loaded data into usable models. Phase 04 wires the working path into Prefect schedules and event chains. Phase 05 expands source variety only after the first path works. Phase 06 makes the system reliable enough to operate. Phase 07 records deferred capabilities in the project specification until a concrete requirement justifies a dedicated implementation phase. Phase 08 reduces repetitive source and entity setup while preserving explicit provider-specific logic. Phase 09 gives AI agents constrained query access to production analytical data without exposing PostgreSQL publicly. Phase 10 imports agent-pipe project-local SQLite records into Felts raw landing. Phase 11 completes source-owned mart coverage for already staged sources and adds Felts-owned internal asset mapping marts without filtering broad provider marts. Phase 12 refreshes the controlled MCP production-data allowlist so the Phase 11 mart surface is available through safe schema-qualified analytical access. Phase 13 captures scheduled CoinGecko OHLC candles for mapped internal crypto assets and exposes the resulting mart through the same controlled access path. Phase 14 adds daily CoinGecko market-chart metrics, corrects OHLC capture to daily interval, schedules broad market snapshots, and exposes daily market metrics plus derived OHLCV marts. Phase 15 fixes the public CoinGecko OHLC path by using 30-day auto-granularity 4-hour candles and deriving daily OHLC rollups in dbt. Phase 16 adds the first CCXT public exchange market snapshot path for Binance `BTC/USDT`, covering ticker and top-20 order book capture, provider-native marts, and mart-only MCP access.

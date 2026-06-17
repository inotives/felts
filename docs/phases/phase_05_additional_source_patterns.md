# Phase 05 - Additional Source Patterns

## Goal

Expand Felts from one REST source into multiple source patterns while preserving the feature-based source structure.

## Core Functionality

- CoinMarketCap REST source with API-key auth.
- DeFi Llama GraphQL source.
- CSV import source using file extraction.
- Shared extraction helpers for auth, cursor pagination, and file batching.

## Scope

- Implement `pipeline/sources/coinmarketcap/`.
- Implement `pipeline/sources/defillama/`.
- Implement `src/felts/sources/csv_import/`.
- Create `graphql_extractor.py`.
- Create `csv_extractor.py`.
- Add raw, staging, intermediary, and mart models only where needed to prove each source pattern.
- Add source-specific schedules after each source works locally.

## Acceptance Criteria

- Each new source follows the same self-contained folder pattern.
- GraphQL and CSV extraction reuse core abstractions without source-specific core changes.
- CoinMarketCap secrets are loaded through settings or Prefect Blocks according to the Phase 06 decision.
- CSV ingestion validates headers before load.
- Cross-source joins are possible in the intermediary layer.

## Out of Scope

- Web UI for CSV import.
- SFTP or object-store upload automation unless selected during grilling.
- WebSocket and Kafka streaming.
- Multi-target warehouse writes.

## Grill Questions

- Which second source provides the highest value after CoinGecko: CoinMarketCap or DeFi Llama?
- Should CSV import start as direct file path, object-store drop, or both?
- Should source additions require a complete mart contribution, or is raw/staging enough?
- How strict should source parity be before adding the next source?

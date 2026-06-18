# Raw Landing Design

Felts lands source data into one schema per source and one raw table per source entity, for example `coingecko.raw_coins_list` and `coingecko.raw_global`. This keeps large raw payload storage physically separated by provider and entity while preserving one shared ingestion contract in code.

Each raw entity table has the same metadata columns plus `payload JSONB`, is a TimescaleDB hypertable on `extracted_at`, and stores schema-invalid but JSON-loadable payloads with validation metadata so retries are idempotent and raw evidence is preserved.

Idempotency remains global through `raw.raw_record_keys`, keyed by deterministic raw record ID. The raw record ID already includes source, entity, source record identity, observation time when available, and payload hash, so a central key table prevents duplicates without requiring every hypertable to carry an id-only unique constraint.

The bootstrap SQL owns only shared raw infrastructure such as `raw.raw_record_keys`. Source schemas and entity raw tables are created on demand by the Postgres loader using the naming pattern `<source>.raw_<entity>`.

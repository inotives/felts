\connect felts

CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION felts;

CREATE TABLE IF NOT EXISTS raw.raw_record_keys (
    id text PRIMARY KEY,
    first_seen_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE raw.raw_record_keys OWNER TO felts;

CREATE TABLE IF NOT EXISTS raw.raw_records (
    id text NOT NULL,
    source text NOT NULL,
    entity text NOT NULL,
    source_record_id text,
    observed_at timestamptz,
    extracted_at timestamptz NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    batch_id text NOT NULL,
    schema_name text,
    schema_version text,
    is_valid boolean NOT NULL,
    validation_errors jsonb NOT NULL DEFAULT '[]'::jsonb,
    payload jsonb NOT NULL,
    CONSTRAINT raw_records_source_format_check CHECK (source ~ '^[a-z0-9_]+$'),
    CONSTRAINT raw_records_entity_format_check CHECK (entity ~ '^[a-z0-9_]+$'),
    CONSTRAINT raw_records_payload_object_check CHECK (jsonb_typeof(payload) = 'object'),
    CONSTRAINT raw_records_validation_errors_array_check
        CHECK (jsonb_typeof(validation_errors) = 'array')
);

ALTER TABLE raw.raw_records OWNER TO felts;

SELECT create_hypertable(
    'raw.raw_records',
    'extracted_at',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS raw_records_id_idx
    ON raw.raw_records (id);

CREATE INDEX IF NOT EXISTS raw_records_source_entity_extracted_at_idx
    ON raw.raw_records (source, entity, extracted_at DESC);

CREATE INDEX IF NOT EXISTS raw_records_batch_id_idx
    ON raw.raw_records (batch_id);

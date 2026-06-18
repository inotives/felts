\connect felts

CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION felts;

CREATE TABLE IF NOT EXISTS raw.raw_record_keys (
    id text PRIMARY KEY,
    first_seen_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE raw.raw_record_keys OWNER TO felts;

-- Source raw landing schemas and entity tables are created on demand by the
-- Postgres loader using the naming pattern <source>.raw_<entity>.

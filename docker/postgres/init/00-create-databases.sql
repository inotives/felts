SELECT 'CREATE ROLE felts LOGIN PASSWORD ''felts'''
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'felts')\gexec

SELECT 'CREATE ROLE prefect LOGIN PASSWORD ''prefect'''
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prefect')\gexec

SELECT 'CREATE DATABASE felts OWNER felts'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'felts')\gexec

SELECT 'CREATE DATABASE prefect OWNER prefect'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'prefect')\gexec

\connect felts

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;

\connect prefect

GRANT ALL PRIVILEGES ON DATABASE prefect TO prefect;

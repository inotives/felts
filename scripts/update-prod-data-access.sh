#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/settings/.env.prod"
ROTATE_AI_PASSWORD=false

for arg in "$@"; do
  case "$arg" in
    --rotate-ai-password)
      ROTATE_AI_PASSWORD=true
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE. Run scripts/deploy-linux-mint.sh first." >&2
  exit 1
fi

cd "$ROOT"

FELTS_AI_PASSWORD="$(sed -n 's/^FELTS_AI_PASSWORD=//p' "$ENV_FILE")"
if [[ -z "$FELTS_AI_PASSWORD" || "$ROTATE_AI_PASSWORD" == true ]]; then
  FELTS_AI_PASSWORD="$(openssl rand -hex 24)"
  if grep -q '^FELTS_AI_PASSWORD=' "$ENV_FILE"; then
    sed -i "s/^FELTS_AI_PASSWORD=.*/FELTS_AI_PASSWORD=$FELTS_AI_PASSWORD/" "$ENV_FILE"
  else
    printf '\nFELTS_AI_PASSWORD=%s\n' "$FELTS_AI_PASSWORD" >> "$ENV_FILE"
  fi
fi

docker compose exec -T postgres psql -U postgres -d postgres -Atqc \
  "SELECT (
     EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'felts')
     AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prefect')
     AND EXISTS (SELECT 1 FROM pg_database WHERE datname = 'felts')
     AND EXISTS (SELECT 1 FROM pg_database WHERE datname = 'prefect')
   )::int" | grep -qx '1'

docker compose exec -T postgres psql -U postgres -d felts \
  -v ai_password="$FELTS_AI_PASSWORD" <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'felts_ai') THEN
    CREATE ROLE felts_ai LOGIN;
  END IF;
END
$$;

ALTER ROLE felts_ai LOGIN PASSWORD :'ai_password';
ALTER ROLE felts_ai SET default_transaction_read_only = on;
ALTER ROLE felts_ai SET statement_timeout = '15s';
ALTER ROLE felts_ai SET idle_in_transaction_session_timeout = '30s';

GRANT CONNECT ON DATABASE felts TO felts_ai;
GRANT USAGE ON SCHEMA public TO felts_ai;

DO $$
DECLARE
  view_name text;
BEGIN
  FOREACH view_name IN ARRAY ARRAY[
    'mart_coingecko__asset_platforms',
    'mart_coingecko__coins',
    'stg_alphavantage__time_series_daily',
    'stg_coingecko__asset_platforms_list',
    'stg_coingecko__coins_list',
    'stg_coingecko__coins_markets',
    'stg_coingecko__global',
    'stg_coingecko__global_defi',
    'stg_csv_import__fred_series',
    'stg_csv_import__ohlcv'
  ]
  LOOP
    IF to_regclass('public.' || view_name) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT ON TABLE public.%I TO felts_ai', view_name);
    END IF;
  END LOOP;
END
$$;
SQL

echo "Updated felts_ai production data access."

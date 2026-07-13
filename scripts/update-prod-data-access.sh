#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/settings/.env.prod"
ALLOWLIST_FILE="$ROOT/settings/felts-prod-data-views.txt"
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

if [[ ! -f "$ALLOWLIST_FILE" ]]; then
  echo "Missing $ALLOWLIST_FILE." >&2
  exit 1
fi

ALLOWED_VIEWS=""
while IFS= read -r view_name || [[ -n "$view_name" ]]; do
  [[ -z "$view_name" || "$view_name" == \#* ]] && continue
  if [[ ! "$view_name" =~ ^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "Malformed allowlist entry in $ALLOWLIST_FILE: $view_name" >&2
    exit 1
  fi
  ALLOWED_VIEWS+="${view_name}"$'\n'
done < "$ALLOWLIST_FILE"

if [[ -z "$ALLOWED_VIEWS" ]]; then
  echo "No allowlisted views found in $ALLOWLIST_FILE." >&2
  exit 1
fi

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
  -v ON_ERROR_STOP=1 \
  -v ai_password="$FELTS_AI_PASSWORD" \
  -v allowed_views="$ALLOWED_VIEWS" <<'SQL'
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

CREATE TEMP TABLE felts_ai_allowed_views(view_ref text);
INSERT INTO felts_ai_allowed_views(view_ref)
SELECT DISTINCT trim(value)
FROM unnest(string_to_array(:'allowed_views', E'\n')) AS value
WHERE trim(value) <> '';

DO $$
DECLARE
  view_ref text;
  view_schema text;
  view_name text;
BEGIN
  FOR view_schema IN
    SELECT DISTINCT split_part(allowed.view_ref, '.', 1)
    FROM felts_ai_allowed_views AS allowed
  LOOP
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = view_schema) THEN
      EXECUTE format('GRANT USAGE ON SCHEMA %I TO felts_ai', view_schema);
    END IF;
  END LOOP;

  FOR view_ref IN SELECT allowed.view_ref FROM felts_ai_allowed_views AS allowed LOOP
    view_schema := split_part(view_ref, '.', 1);
    view_name := split_part(view_ref, '.', 2);
    IF to_regclass(format('%I.%I', view_schema, view_name)) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO felts_ai', view_schema, view_name);
    END IF;
  END LOOP;
END
$$;
SQL

echo "Updated felts_ai production data access."

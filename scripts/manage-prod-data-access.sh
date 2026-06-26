#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
  disable)
    ACTION="NOLOGIN"
    ;;
  enable)
    ACTION="LOGIN"
    ;;
  *)
    echo "Usage: $0 disable|enable" >&2
    exit 1
    ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

sudo docker compose exec -T postgres psql -U postgres -d felts \
  -v action="$ACTION" <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'felts_ai') THEN
    RAISE EXCEPTION 'role felts_ai does not exist';
  END IF;
END
$$;

ALTER ROLE felts_ai :action;
SQL

echo "felts_ai set to $ACTION"

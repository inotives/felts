#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -eq 0 ]]; then
  echo "Run this script as your SSH user, not with sudo. It requests sudo when needed." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_USER="$USER"
DEPLOY_GROUP="$(id -gn "$DEPLOY_USER")"
DEPLOY_HOME="$(getent passwd "$DEPLOY_USER" | cut -d: -f6)"
ENV_FILE="$ROOT/settings/.env.prod"
PROFILE_FILE="$ROOT/transforms/profiles.yml"
HOST_IP="${FELTS_HOST:-$(hostname -I | awk '{print $1}')}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$ROOT")}"
POSTGRES_VOLUME="${COMPOSE_PROJECT_NAME}_felts-postgres-data"

if [[ "$#" -gt 0 ]]; then
  echo "Usage: $0" >&2
  echo "Use scripts/update-prod-data-access.sh --rotate-ai-password for MCP access rotation." >&2
  exit 1
fi

if [[ -z "$HOST_IP" ]]; then
  echo "Unable to detect the host IP. Run with FELTS_HOST=192.168.1.50." >&2
  exit 1
fi

wait_for_postgres_bootstrap() {
  for _ in {1..60}; do
    if sudo docker compose exec -T postgres psql -U postgres -d postgres -Atqc \
      "SELECT (
         EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'felts')
         AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prefect')
         AND EXISTS (SELECT 1 FROM pg_database WHERE datname = 'felts')
         AND EXISTS (SELECT 1 FROM pg_database WHERE datname = 'prefect')
       )::int" 2>/dev/null \
      | grep -qx '1'; then
      return 0
    fi
    sleep 2
  done

  echo "Postgres started, but required Felts roles/databases are missing." >&2
  echo "Refusing to continue because this may indicate an empty or wrong production volume." >&2
  return 1
}

sudo apt-get update
sudo apt-get install -y ca-certificates curl git openssl

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  if apt-cache show docker-ce >/dev/null 2>&1; then
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
      docker-compose-plugin
  else
    sudo apt-get install -y docker.io docker-compose-v2
  fi
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "$DEPLOY_USER"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

UV_BIN="$(command -v uv || true)"
if [[ -z "$UV_BIN" && -x "$DEPLOY_HOME/.local/bin/uv" ]]; then
  UV_BIN="$DEPLOY_HOME/.local/bin/uv"
fi
if [[ -z "$UV_BIN" ]]; then
  echo "uv installation failed." >&2
  exit 1
fi

cd "$ROOT"
"$UV_BIN" python install 3.12
"$UV_BIN" sync --frozen --python 3.12 --group orchestration --group dbt --group postgres

if [[ ! -f "$ENV_FILE" ]]; then
  FELTS_DB_PASSWORD="$(openssl rand -hex 24)"
  PREFECT_DB_PASSWORD="$(openssl rand -hex 24)"
  POSTGRES_ADMIN_PASSWORD="$(openssl rand -hex 24)"
  cat > "$ENV_FILE" <<EOF
FELTS_ENV=prod
FELTS_DB_HOST=127.0.0.1
FELTS_DB_PORT=5432
FELTS_DB_NAME=felts
FELTS_DB_USER=felts
FELTS_DB_PASSWORD=$FELTS_DB_PASSWORD
FELTS_DATABASE_URL=postgresql+psycopg://felts:$FELTS_DB_PASSWORD@127.0.0.1:5432/felts
POSTGRES_ADMIN_PASSWORD=$POSTGRES_ADMIN_PASSWORD

PREFECT_API_URL=http://$HOST_IP:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:$PREFECT_DB_PASSWORD@127.0.0.1:5432/prefect
PREFECT_CLIENT_CSRF_SUPPORT_ENABLED=false

FELTS_PREFECT_WORK_POOL=production
FELTS_PREFECT_WORK_POOL_TYPE=process
FELTS_PREFECT_WORK_QUEUE=default

COINGECKO_API_KEY=${COINGECKO_API_KEY:-}
EOF
  chmod 600 "$ENV_FILE"
else
  if ! sudo docker volume inspect "$POSTGRES_VOLUME" >/dev/null 2>&1; then
    echo "$ENV_FILE exists, but Docker volume $POSTGRES_VOLUME is missing." >&2
    echo "Refusing to start Postgres because that would create an empty production volume." >&2
    exit 1
  fi
  FELTS_DB_PASSWORD="$(sed -n 's/^FELTS_DB_PASSWORD=//p' "$ENV_FILE")"
  POSTGRES_ADMIN_PASSWORD="$(sed -n 's/^POSTGRES_ADMIN_PASSWORD=//p' "$ENV_FILE")"
  PREFECT_DATABASE_URL="$(sed -n 's/^PREFECT_API_DATABASE_CONNECTION_URL=//p' "$ENV_FILE")"
  PREFECT_DB_PASSWORD="${PREFECT_DATABASE_URL#*://prefect:}"
  PREFECT_DB_PASSWORD="${PREFECT_DB_PASSWORD%@*}"
  if [[ -z "$POSTGRES_ADMIN_PASSWORD" ]]; then
    POSTGRES_ADMIN_PASSWORD="$(openssl rand -hex 24)"
    printf '\nPOSTGRES_ADMIN_PASSWORD=%s\n' "$POSTGRES_ADMIN_PASSWORD" >> "$ENV_FILE"
  fi
  if [[ -z "$FELTS_DB_PASSWORD" || -z "$PREFECT_DB_PASSWORD" ]]; then
    echo "$ENV_FILE exists but does not contain production database passwords." >&2
    exit 1
  fi
fi

cp -n transforms/profiles.yml.example "$PROFILE_FILE"
chmod 600 "$PROFILE_FILE"

sudo docker compose up -d --build postgres
until sudo docker compose exec -T postgres pg_isready -U postgres -d postgres >/dev/null; do
  sleep 2
done
wait_for_postgres_bootstrap
sudo docker compose exec -T postgres psql -U postgres -d postgres \
  -v felts_password="$FELTS_DB_PASSWORD" \
  -v prefect_password="$PREFECT_DB_PASSWORD" \
  -v postgres_password="$POSTGRES_ADMIN_PASSWORD" <<'SQL'
ALTER ROLE felts PASSWORD :'felts_password';
ALTER ROLE prefect PASSWORD :'prefect_password';
ALTER ROLE postgres PASSWORD :'postgres_password';
SQL
sudo docker compose exec -T postgres psql -U postgres -d felts \
  < docker/postgres/init/10-create-raw-records.sql

sudo tee /etc/systemd/system/felts-prefect-server.service >/dev/null <<EOF
[Unit]
Description=Felts Prefect server
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_GROUP
SupplementaryGroups=docker
WorkingDirectory=$ROOT
EnvironmentFile=$ENV_FILE
Environment=PATH=$DEPLOY_HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$UV_BIN run prefect server start --host 0.0.0.0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/felts-prefect-worker.service >/dev/null <<EOF
[Unit]
Description=Felts Prefect worker
Requires=felts-prefect-server.service
After=felts-prefect-server.service

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_GROUP
SupplementaryGroups=docker
WorkingDirectory=$ROOT
EnvironmentFile=$ENV_FILE
Environment=PATH=$DEPLOY_HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$UV_BIN run prefect worker start --pool production --work-queue default
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable felts-prefect-server
sudo systemctl restart felts-prefect-server

echo "Waiting for Prefect at http://$HOST_IP:4200/api ..."
for _ in {1..60}; do
  if curl -fsS "http://$HOST_IP:4200/api/health" >/dev/null; then
    break
  fi
  sleep 2
done
curl -fsS "http://$HOST_IP:4200/api/health" >/dev/null

"$UV_BIN" run --env-file "$ENV_FILE" python -m felts.schedules.orchestrator

sudo systemctl enable felts-prefect-worker
sudo systemctl restart felts-prefect-worker

"$UV_BIN" run --env-file "$ENV_FILE" dbt debug \
  --project-dir transforms \
  --profiles-dir transforms

sudo systemctl --no-pager --full status felts-prefect-server
sudo systemctl --no-pager --full status felts-prefect-worker
sudo docker compose ps

cat <<EOF

Felts deployment complete.
Prefect UI: http://$HOST_IP:4200
Settings: $ENV_FILE

Optional LAN firewall rule:
  sudo ufw allow from <YOUR_LAN_CIDR> to any port 4200 proto tcp
EOF

# Linux Mint Production Deployment

Felts can be deployed to one Linux Mint machine with one script after cloning the
repository.

## What the Script Does

`scripts/deploy-linux-mint.sh`:

- Installs Docker and basic system packages.
- Installs `uv` and Python 3.12.
- Installs Felts runtime dependencies.
- Generates production database passwords on the first run.
- Writes the uncommitted `settings/.env.prod`.
- Starts and bootstraps Dockerized Postgres.
- Restricts Postgres to `127.0.0.1`.
- Installs Prefect server and worker as systemd services.
- Registers work pools, deployments, schedules, and automations.
- Runs `dbt debug`.
- Preserves existing production settings when rerun.

The script uses the current SSH user for the services. Run it as that user, not as
root and not with `sudo`. It requests `sudo` when required.

## Deploy

SSH to the Linux Mint machine:

```bash
ssh <USER>@<LINUX_MINT_IP>
```

Clone and deploy:

```bash
git clone git@github.com:inotives/felts.git
cd felts
bash scripts/deploy-linux-mint.sh
```

If automatic IP detection selects the wrong network interface:

```bash
FELTS_HOST=192.168.1.50 bash scripts/deploy-linux-mint.sh
```

Provide the CoinGecko key during first deployment:

```bash
COINGECKO_API_KEY=<KEY> bash scripts/deploy-linux-mint.sh
```

The script prints the Prefect URL when complete:

```text
http://<LINUX_MINT_IP>:4200
```

## Network Access

Postgres listens only on the Linux machine's loopback interface. Do not expose port
`5432`.

If UFW is enabled, allow Prefect only from the local subnet:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 4200 proto tcp
```

Replace the subnet with the actual LAN range.

Prefect does not currently have authentication or TLS in this deployment. Port `4200`
must not be forwarded to the internet.

## Verify

```bash
systemctl status felts-prefect-server
systemctl status felts-prefect-worker
sudo docker compose ps
```

Run a small source ingestion:

```bash
uv run --env-file settings/.env.prod felts coingecko run --entities coins_list global
```

Run dbt:

```bash
uv run --env-file settings/.env.prod dbt run \
  --project-dir transforms \
  --profiles-dir transforms

uv run --env-file settings/.env.prod dbt test \
  --project-dir transforms \
  --profiles-dir transforms
```

## Update

Stop the worker, update the repository, and rerun the same script:

```bash
sudo systemctl stop felts-prefect-worker
git pull --ff-only origin main
bash scripts/deploy-linux-mint.sh
```

The script keeps the existing database volume and `settings/.env.prod`.

## Logs

```bash
journalctl -u felts-prefect-server -f
journalctl -u felts-prefect-worker -f
sudo docker compose logs -f postgres
```

## Production Settings

Generated secrets and configuration live in:

```text
settings/.env.prod
```

The file is uncommitted and mode `600`. Edit it to change the CoinGecko key or other
production settings, then restart services:

```bash
sudo systemctl restart felts-prefect-server felts-prefect-worker
```

Re-register Prefect after changing schedules, deployments, automations, CSV contracts,
or dbt selectors:

```bash
uv run --env-file settings/.env.prod python -m felts.schedules.orchestrator
```

## Backup

Back up both databases:

```bash
mkdir -p backups

sudo docker compose exec -T postgres pg_dump -U postgres -Fc felts \
  > "backups/felts-$(date +%F-%H%M%S).dump"

sudo docker compose exec -T postgres pg_dump -U postgres -Fc prefect \
  > "backups/prefect-$(date +%F-%H%M%S).dump"
```

Copy backups to another machine or storage device. Backups kept only on the Linux Mint
machine do not protect against disk failure.

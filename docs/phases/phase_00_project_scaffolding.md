# Phase 00 - Project Scaffolding

## Goal

Create the Felts project skeleton so later phases have a consistent package layout, tooling baseline, and development workflow.

## Core Functionality

- Python project metadata and dependency management with `uv`.
- Python 3.12 as the project baseline.
- `.python-version` file for local Python version consistency.
- `.gitignore` for Python, `uv`, dbt, Docker, and local environment artifacts.
- `.dockerignore` for Docker build contexts.
- Committed `uv.lock` for reproducible application installs.
- Local virtual environment created at `.venv`.
- Pandas as the default Python-side tabular data library.
- Monorepo-compatible Python package layout under `src/felts/`.
- Test folder layout split into unit and integration tests.
- Local environment template.
- Project-level configuration through `.env` and `pydantic-settings`, including repo paths such as the dbt project directory.
- Dockerized Postgres for local development.
- Dockerized Postgres based on TimescaleDB with `pgvector` installed and enabled for vector workloads.
- Custom local Postgres image based on the official TimescaleDB image with `pgvector` installed.
- Docker healthcheck for local Postgres readiness.
- Named Docker volume for local Postgres data persistence.
- Local Prefect server configured to use Dockerized Postgres instead of Prefect's default SQLite database.
- Docker Compose kept to Postgres only for Phase 00.
- Basic developer commands for formatting, linting, tests, and dbt/Prefect placeholders.
- Simple Makefile as the project-level command facade.
- Root README as the developer entry point for local setup commands.
- Root `AGENTS.md` for agent coding guidelines.
- Ruff-only linting and formatting.
- Minimal CI for dependency sync, Ruff checks, and smoke tests.
- GitHub Actions as the initial CI provider.
- Prefect installed and documented for local development, without implementing flows or deployments yet.
- Empty module boundaries for core, sources, flows, schedules, transforms, and config.

## Scope

- Create Python project config in `pyproject.toml`.
- Pin the project Python baseline to Python 3.12.
- Create `.python-version` with the Python 3.12 baseline.
- Create `.gitignore` that excludes generated/local artifacts while keeping `.env.example` and `uv.lock` tracked.
- Ignore `transforms/profiles.yml` while tracking `transforms/profiles.yml.example`.
- Create `.dockerignore` that excludes virtualenvs, local env files, caches, Git metadata, and dbt build artifacts.
- Generate and commit `uv.lock`.
- Standardize dependency installation and command execution through `uv`.
- Create the project virtual environment at `.venv`.
- Create `src/felts/` package and top-level `__init__.py` files.
- Create package directories for `core/`, `sources/`, `flows/`, `schedules/`, and `config/` with `__init__.py` files only.
- Do not create placeholder implementation modules before their contracts are defined.
- Create `tests/unit/` and `tests/integration/` directories.
- Leave `tests/integration/` empty until Phase 01 introduces real database-backed behavior.
- Keep room for sibling monorepo packages or apps outside `src/felts/`.
- Do not create speculative top-level `apps/`, `packages/`, or `tools/` directories until a real Next.js app, Rust package/tool, or other sibling component exists.
- Create top-level `transforms/` for the dbt project.
- Initialize an empty dbt project shell under `transforms/` with `dbt_project.yml`, `profiles.yml.example`, and empty `models/`, `macros/`, `tests/`, and `seeds/` directories.
- Do not commit a real `transforms/profiles.yml`; keep only `profiles.yml.example` tracked.
- Use environment variables with local defaults in `profiles.yml.example`.
- Define project-level config values through `.env.example` and `pydantic-settings`; do not introduce a committed `felts.toml` yet.
- Create initial dependency groups for runtime, development, dbt, and optional warehouse adapters.
- Create dependency groups for runtime, development, orchestration, dbt, Postgres, and financial analysis/source libraries.
- Include `pandas` in the main runtime dependencies.
- Document local development setup with all dependency groups installed through `uv`.
- Create `.env.example` with non-secret configuration names.
- Define baseline environment variables for Felts database access, Prefect API/database settings, and dbt project/profile paths.
- Include `COINGECKO_API_KEY` as the only source-specific placeholder in Phase 00.
- Treat CoinGecko and CSV import as initial planned sources, but do not create source-specific packages in Phase 00.
- Use `csv_import` as the canonical name for the initial CSV source in later phases.
- Create Docker Compose configuration for local Postgres.
- Place `docker-compose.yml` at the repository root.
- Configure Postgres with a named Docker volume.
- Add a Postgres readiness healthcheck to Docker Compose.
- Do not add Adminer, pgAdmin, or other local database UI containers in Phase 00.
- Create `docker/postgres/Dockerfile` for the custom TimescaleDB plus `pgvector` image.
- Create local database initialization SQL files under `docker/postgres/init/`.
- Use TimescaleDB as the local Postgres base image.
- Install and enable `pgvector` in the local database image or initialization flow.
- Create separate local Postgres databases in the same container: `felts` for application data and `prefect` for Prefect orchestration metadata.
- Create separate local Postgres users for the `felts` and `prefect` databases.
- Document Prefect environment settings so the local server connects to the Dockerized Postgres database.
- Initialize only local databases and required extensions in Phase 00; defer application schemas such as `raw`, `staging`, `intermediary`, and `mart`.
- Create README or developer notes for local setup commands.
- Keep the README concise; project rationale and detailed planning stay in `docs/`.
- Document the first-run happy path in the README with `make install` and `make check`.
- Keep `AGENTS.md` as the canonical local agent guidance document.
- Create a small Makefile for common local commands such as `venv`, `install`, `lint`, `format`, `test`, `check`, `db-up`, `db-down`, `db-shell`, `db-check`, `dbt-debug`, `prefect-check`, and `prefect-server`.
- Make `prefect-server` depend on `db-up` because local Prefect uses the Dockerized Postgres database.
- Add Ruff formatter/linter configuration and test runner configuration.
- Add minimal CI configuration for `uv sync --all-groups`, `ruff check`, `ruff format --check`, and smoke tests.
- Create `.github/workflows/ci.yml` for the minimal CI workflow.
- Keep Phase 00 CI focused on Python dependency, lint, format, and test checks only.
- Add Prefect dependency and basic local setup notes.
- Add lightweight local Prefect profile/setup documentation for API URL and Postgres-backed server configuration.
- Add minimal unit smoke test proving the package imports.

## Acceptance Criteria

- A new developer can create `.venv` and install dependencies using `uv`.
- Dependency groups are defined for `dev`, `orchestration`, `dbt`, `postgres`, and `finance`.
- Local development setup installs all dependency groups by default, while CI/minimal workflows may install narrower groups.
- `uv.lock` is present and treated as a tracked reproducibility artifact.
- Common local setup and verification commands are available through Makefile targets.
- `make prefect-server` ensures local Postgres is running before starting Prefect.
- `make db-shell` opens `psql` inside the Postgres container without requiring host `psql`.
- `make db-check` verifies that TimescaleDB and `pgvector` extensions are installed in the local Felts database.
- `make dbt-debug` verifies dbt project/profile configuration and local Postgres connectivity.
- `make prefect-check` verifies Prefect installation and local configuration without starting a long-running server.
- `make check` runs all non-long-running verification commands for the scaffold, including database-backed checks.
- Root README documents the current local setup workflow without duplicating the full project spec.
- Root README includes a one-command scaffold verification path through `make check`.
- Root `AGENTS.md` exists and captures agent coding guidelines for future implementation work.
- `felts` imports successfully from the installed package.
- Runtime code can resolve the dbt project directory from project-level config rather than hard-coded flow paths.
- `transforms/` exists as a valid dbt project shell, but contains no transformation models yet.
- `profiles.yml.example` is runnable locally through environment variables and defaults without committing credentials.
- Dockerized Postgres starts locally from the documented command.
- Local Postgres data persists across normal container restarts.
- Docker Compose reports Postgres as healthy once it is ready for connections.
- The local Postgres instance supports TimescaleDB and `pgvector` extensions.
- TimescaleDB is available as infrastructure, but Phase 00 does not require every table to be a hypertable.
- The local database bootstrap does not create application schemas yet.
- Local Prefect server uses the Dockerized Postgres database for orchestration metadata, not SQLite.
- `.env.example` exposes separate database URLs for Felts application data and Prefect orchestration metadata.
- `.env.example` includes baseline variables such as `FELTS_ENV`, `FELTS_DATABASE_URL`, `PREFECT_API_URL`, `PREFECT_API_DATABASE_CONNECTION_URL`, `FELTS_DBT_PROJECT_DIR`, and `FELTS_DBT_PROFILES_DIR`.
- `.env.example` includes `COINGECKO_API_KEY` and defers other source-specific secrets until those sources are implemented.
- Local Prefect configuration can be applied from documented commands and `.env.example` values.
- Test runner executes at least one unit smoke test.
- Minimal CI runs dependency installation, linting, formatting check, and smoke tests.
- Minimal CI is implemented as a GitHub Actions workflow.
- Directory layout supports a monorepo while keeping Felts' Python package isolated under `src/felts/`.
- Future Rust tools, shared packages, or Next.js apps can be added later under `tools/`, `packages/`, or `apps/` when they have a concrete use case.
- No real source, loader, dbt, or Prefect behavior is implemented yet.

## Out of Scope

- Base extractor and loader contracts.
- Raw record schema.
- Postgres loader behavior.
- Source-specific implementation.
- dbt models.
- Real dbt model implementations; start these in Phase 03.
- Prefect flows, deployments, and automations.
- A separate committed `felts.toml` config file.
- Black, isort, Flake8, or other overlapping Python lint/format tools.
- Static type-checker enforcement; add this in Phase 01 after the core contracts exist.
- Adminer, pgAdmin, or other local database UI services.
- Python-based database bootstrap command.
- Destructive database reset Makefile target.
- Application schemas such as `raw`, `staging`, `intermediary`, and `mart`.
- Database, dbt, and Prefect integration CI; defer to later phases.
- Markdown formatting or linting checks.
- Real source integrations using CCXT, yfinance, or other finance libraries.
- Source-specific packages such as `sources/coingecko/` or `sources/csv_import/`; add them in the source implementation phase.
- Polars; add it later only if a large-file or performance-heavy use case requires it.
- TA-Lib; add it later only if technical-indicator work requires it.
- Production database image hardening.
- `LICENSE` and `CONTRIBUTING.md`; defer until the project is ready to publish or accept external contribution.
- Pre-commit hooks; use explicit Makefile and CI checks for Phase 00.
- Empty speculative monorepo folders such as `apps/`, `packages/`, or `tools/`.
- Placeholder implementation modules inside `core`, `sources`, `flows`, or `schedules`.
- Placeholder integration tests without real integration behavior.
- Coverage tooling and coverage thresholds; defer until meaningful implementation tests exist.

## Grill Questions

- Are there any remaining Phase 00 scaffolding decisions to resolve before implementation?

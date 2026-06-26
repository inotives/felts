# Phase 09 - Production Data Agent Access

## Goal

Allow authorized AI agents, initially Codex and OpenCode, to query selected Felts
production PostgreSQL data through one MCP-compatible interface without exposing
PostgreSQL on the LAN or granting mutation privileges.

## Existing Constraints

- Production PostgreSQL remains bound to `127.0.0.1:5432` on the Linux machine.
- Port `5432` is not opened through UFW or otherwise exposed to the LAN.
- The MCP server runs on the agent/Codex machine, not on the production Linux
  machine.
- The MCP server reaches production PostgreSQL through an SSH tunnel to
  `inotives@192.168.50.182`.
- MCP availability is independent of the always-on production ingestion pipelines;
  the MCP server and tunnel run only when agent access is needed.
- Agent access uses a dedicated PostgreSQL role rather than application or
  administrator credentials.
- The agent may query views in the `public` schema, including dbt staging and mart
  views.
- Raw source schemas and raw provider payload tables are excluded.
- Access is granted to views rather than broadly to every current or future object in
  `public`.
- Agent access is on-demand. The SSH tunnel and MCP server are started explicitly for
  an interactive agent session and are not installed as persistent background services.
- A single local launcher owns the access-session lifecycle:
  - starts an SSH local-forward from `127.0.0.1:15432` to production
    `127.0.0.1:5432`;
  - fails clearly if local port `15432` is already occupied;
  - verifies PostgreSQL connectivity before starting the MCP server;
  - stops its SSH tunnel when the MCP server exits or startup fails.
- The MCP interface permits arbitrary analytical `SELECT` queries rather than only
  predefined dataset operations.
- Read-only behavior is enforced independently by the PostgreSQL role and connection
  defaults; prompt instructions are not treated as a security boundary.
- The MCP layer also applies bounded result sizes and rejects multi-statement or
  mutation-oriented requests before sending them to PostgreSQL.
- Query safety limits:
  - maximum 1,000 returned rows;
  - 15-second PostgreSQL statement timeout;
  - 30-second idle-in-transaction timeout;
  - non-aggregate row-returning queries require an explicit `LIMIT`;
  - aggregate-only queries may omit `LIMIT`.
- Local access credentials are stored in an ignored `.env` file rather than macOS
  Keychain.
- The `.env` file contains only the dedicated read-only PostgreSQL credential and MCP
  access configuration; production application or administrator credentials are not
  reused.
- The launcher loads the credential into the MCP process environment and does not place
  it in command-line arguments or committed configuration.
- The MCP server writes a local metadata-only audit log for each query containing:
  timestamp, duration, returned row count, and success or failure.
- Audit logs exclude credentials and returned result data.
- Audit log retention is 30 days.
- Audit records are written as JSON Lines to ignored
  `var/log/felts-prod-data/queries.jsonl`.
- Launcher startup removes audit files older than 30 days.
- Audit records store a SHA-256 hash of normalized SQL rather than SQL text.
- SQL literals and query result data are not retained in audit logs.
- Felts owns a small MCP server rather than exposing a generic PostgreSQL MCP directly.
- The initial MCP tool surface is limited to:
  - `list_views`;
  - `describe_view`;
  - `query`.
- `query` returns:
  - ordered column metadata;
  - rows as JSON-compatible values;
  - `row_count`;
  - `truncated`.
- SQL `NULL` and boolean values are preserved; dates, timestamps, and decimals are
  serialized as strings to avoid precision or timezone loss.
- The server fetches at most 1,001 rows, returns the first 1,000, and sets
  `truncated=true` when the additional row exists.
- Truncation detection does not execute a separate count query.
- The Felts-owned server is the policy boundary for the view allowlist, query validation,
  result limits, and audit logging.
- The MCP server is implemented in Python using the official MCP Python SDK.
- MCP dependencies live in a dedicated optional `mcp` dependency group so production
  ingestion and orchestration installations do not require them.
- The project continues to use `uv` for installation and execution.
- SQL validation uses `sqlglot` from the optional `mcp` dependency group, parsed with
  the PostgreSQL dialect.
- The validator uses the parsed AST, not regex-only checks, to enforce the top-level
  statement type, view allowlist, safe function allowlist, and `LIMIT` policy.
- Codex and OpenCode use the same MCP server, launcher, SSH tunnel, policy, and
  credentials; Phase 09 does not create client-specific server implementations.
- The MCP is registered globally in both Codex and OpenCode because approved consumers
  include workspaces outside this repository, such as `~/.strata-memory`.
- Both global registrations invoke the same launcher versioned in the Felts repository;
  configuration and credentials are not duplicated into consumer workspaces.
- The committed launcher script is `scripts/felts-prod-data-mcp`.
- Codex and OpenCode global MCP registrations point to `scripts/felts-prod-data-mcp`;
  their client configs do not contain PostgreSQL credentials or SSH secrets.
- The launcher owns the local lifecycle: load `.env`, start the SSH tunnel, verify
  PostgreSQL readiness, execute the MCP server, and clean up its own tunnel on exit.
- The MCP is identified as Felts production analytical data so agents do not confuse it
  with a general-purpose local PostgreSQL connection.
- The canonical MCP registration name is `felts-prod-data` in both Codex and OpenCode.
- Allowed views are defined by an explicit committed allowlist.
- `list_views` returns only allowlisted views; it does not expose every object discovered
  in `public`.
- New dbt views require deliberate review and an allowlist change before agents can
  discover, describe, or query them.
- The initial allowlist contains:
  - `mart_coingecko__asset_platforms`;
  - `mart_coingecko__coins`;
  - `stg_alphavantage__time_series_daily`;
  - `stg_coingecko__asset_platforms_list`;
  - `stg_coingecko__coins_list`;
  - `stg_coingecko__coins_markets`;
  - `stg_coingecko__global`;
  - `stg_coingecko__global_defi`;
  - `stg_csv_import__fred_series`;
  - `stg_csv_import__ohlcv`.
- Future analytical views can be added through a reviewed allowlist-only change; this
  does not require a new MCP tool or protocol change.
- `describe_view` returns:
  - column names in ordinal order;
  - PostgreSQL data types;
  - nullability;
  - the dbt model description;
  - dbt column descriptions when present.
- Missing dbt descriptions are represented as absent metadata rather than inferred by
  the MCP server.
- `query` accepts exactly one SQL statement whose top-level operation is `SELECT` or
  `WITH ... SELECT`.
- The server rejects:
  - SQL comments and semicolons;
  - data-modifying CTEs;
  - `SELECT INTO`;
  - references outside allowlisted `public` views;
  - function calls outside an explicit safe set.
- PostgreSQL read-only privileges and connection defaults remain the final security
  backstop if MCP validation is bypassed or incorrect.
- The initial safe SQL function allowlist is:
  - aggregates: `count`, `sum`, `avg`, `min`, `max`;
  - numeric: `round`, `abs`;
  - null handling: `coalesce`, `nullif`;
  - date/time: `date_trunc`, `extract`;
  - window functions: `row_number`, `rank`, `dense_rank`, `lag`, `lead`.
- Additional functions require a reviewed policy change driven by a concrete query need.
- SSH uses normal `known_hosts` verification and fails for unknown or changed host
  keys.
- The launcher does not disable host-key checking or silently accept a new host key.
- `scripts/deploy-linux-mint.sh` idempotently provisions the dedicated `felts_ai`
  PostgreSQL login.
- The deployment script:
  - generates the role password on first provisioning and preserves it on reruns;
  - stores it only in production `settings/.env.prod`;
  - applies read-only connection defaults and query timeouts;
  - grants database connection and schema usage;
  - grants `SELECT` only on the committed allowlisted views;
  - revokes obsolete view grants when an allowlisted view is removed.
- The operator copies the generated `felts_ai` credential once into the ignored local
  MCP `.env`; deployment does not transmit credentials to the agent machine.
- Normal deployment reruns preserve the existing `felts_ai` password.
- An explicit rotation option generates and applies a new password; the operator then
  updates `settings/.env.mcp.local` manually.
- Revocation uses `ALTER ROLE felts_ai NOLOGIN` without deleting the role or grants.
- Re-enabling access uses `ALTER ROLE felts_ai LOGIN` after operator approval.
- Operator commands are:
  - `scripts/deploy-linux-mint.sh` for normal idempotent provisioning;
  - `scripts/deploy-linux-mint.sh --rotate-ai-password` for explicit credential rotation;
  - `scripts/manage-prod-data-access.sh disable` to revoke login;
  - `scripts/manage-prod-data-access.sh enable` to restore login.
- Local MCP configuration lives in ignored `settings/.env.mcp.local`.
- A committed `settings/.env.mcp.example` documents required variable names without
  values.
- The shared launcher loads `settings/.env.mcp.local` for both Codex and OpenCode.
- The local MCP `.env` contract is:
  - `FELTS_MCP_SSH_HOST=192.168.50.182`;
  - `FELTS_MCP_SSH_USER=inotives`;
  - `FELTS_MCP_SSH_PORT=22`;
  - `FELTS_MCP_LOCAL_PORT=15432`;
  - `FELTS_MCP_REMOTE_HOST=127.0.0.1`;
  - `FELTS_MCP_REMOTE_PORT=5432`;
  - `FELTS_MCP_DB_NAME=felts`;
  - `FELTS_MCP_DB_USER=felts_ai`;
  - `FELTS_MCP_DB_PASSWORD`;
  - `FELTS_MCP_AUDIT_LOG=var/log/felts-prod-data/queries.jsonl`.
- Tunnel startup uses an existing SSH key or SSH agent and must be non-interactive.
- The launcher does not read, prompt for, or store the Linux SSH account password.
- If `127.0.0.1:15432` is already occupied, the launcher fails clearly and does not
  reuse or terminate the unknown process.
- After creating the tunnel, the launcher retries PostgreSQL readiness for at most
  10 seconds and then exits with a clear error.
- Startup does not retry indefinitely.
- The initial capability is read-only.
- Credentials and private keys are never committed.

## Decisions to Resolve

- Query safety limits, auditing, credential rotation, and revocation.
- Deployment, verification, and acceptance criteria.

## Acceptance Criteria

- Phase planning docs and ADRs are committed to `main` before the implementation branch is
  created.
- The implementation PR includes the MCP server, shared launcher, `.env` example,
  committed allowlist, tests, deployment role provisioning, and Codex/OpenCode
  registration notes.
- Both Codex and OpenCode can invoke the globally registered `felts-prod-data` MCP.
- Codex is verified locally through its MCP registration.
- If OpenCode is available locally, OpenCode is verified through its MCP registration; if
  not, the PR documents the exact manual registration and verification steps.
- Each client can list exactly the committed allowlisted views.
- Each client can describe at least:
  - `stg_alphavantage__time_series_daily`;
  - `mart_coingecko__coins`.
- Each client can run a bounded aggregate query against production and receive the
  documented JSON-compatible result contract.
- The MCP rejects:
  - a query referencing a raw source table;
  - a mutation statement;
  - a non-aggregate row-returning query without `LIMIT`;
  - a query using a non-allowlisted function.
- The PostgreSQL `felts_ai` role cannot mutate data when tested independently of MCP
  validation.
- The launcher exits cleanly and removes only the SSH tunnel process that it created.
- PostgreSQL remains bound to production loopback and port `5432` is not exposed on the
  LAN.
- Audit records contain query hashes and metadata but no SQL text, result data, or
  credentials.
- Unit tests cover SQL policy validation, view allowlisting, result serialization,
  truncation, auditing, and launcher failure cleanup.

## Out of Scope Until Explicitly Approved

- Agent writes to production data.
- Public PostgreSQL exposure.
- Giving the agent production application or PostgreSQL administrator credentials.
- General shell access to the production Linux machine through the database tool.

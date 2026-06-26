# Phase 08 - Source and Entity Scaffolding

## Goal

Reduce the repetitive work required to add:

- A new Source pipeline.
- A new Entity endpoint to an existing Source.

The intended interface is one repository script with explicit subcommands. It should
generate the minimum consistent files and checklist needed for implementation without
pretending that provider-specific extraction, schemas, or dbt logic can be inferred
reliably.

## Current Friction

Adding a new Source currently requires coordinating:

- A feature package under `src/felts/sources/<source>/`.
- CLI registration.
- Extractor, schemas, runner, flow, events, deployments, and automations.
- Orchestrator registration.
- dbt source declarations and staging models.
- Unit and integration test locations.
- Environment templates and documentation when credentials are required.

Adding an Entity to CoinGecko currently requires coordinated edits to:

- The entity type and supported entity registry.
- Endpoint metadata.
- Extractor dispatch and extraction behavior.
- Pydantic schema registration.
- dbt selector mapping.
- Optional schedule registration.
- dbt source and staging models.
- Tests for extraction, runner behavior, events, deployments, and models.

Missing one registration point can leave a partially working pipeline.

## Candidate Interface

```bash
scripts/scaffold.py source <source> --base-url <url>
scripts/scaffold.py entity <source> <entity> \
  --path <endpoint-path> \
  --response-shape <list|object|data_object|keyed_object> \
  [--records-path <response-key>] \
  [--key-field <payload-field>] \
  [--id-field <field>]... \
  [--param <key=value>]... \
  [--runtime-param <name>]...
```

The exact inputs and generated files remain subject to grilling.

## Initial Constraints

- The scaffold generates files, runs fast local validation, and prints next steps.
- It does not register Prefect deployments, modify production settings, or deploy
  generated code.
- Phase 08 supports REST Sources and REST Entities only.
- CSV remains YAML contract-driven and is not handled by this scaffold.
- A new REST Source requires only a normalized source name and base URL.
- Authentication, entities, schemas, dbt models, and schedules remain explicit
  follow-up work rather than interactive scaffold questions.
- A new REST Entity requires a normalized entity name, endpoint path, and response
  shape.
- Supported response shapes are `list`, `object`, `data_object`, and `keyed_object`.
- `keyed_object` requires a records path and key field. Each entry in the selected
  response mapping becomes one ExtractedRecord, and the mapping key is copied into the
  declared payload field.
- Runtime parameter values are copied into each generated record payload so they remain
  available for identity and dbt modeling.
- Source identity fields are optional, repeatable, and ordered.
- The generated extractor builds a deterministic source record ID from the declared
  identity field values.
- Missing declared identity values produce an invalid record with validation details;
  they do not silently share an identity.
- Repeatable static query parameters are supported as `--param key=value`.
- Repeatable runtime parameter names are supported as `--runtime-param <name>`.
- Generated CLI and Prefect flow parameters require values for declared runtime
  parameters.
- A Source Run may accept multiple values for one runtime parameter and execute one
  request per value.
- Pagination is not generated in Phase 08. Entities requiring pagination receive an
  explicit next-step marker for custom extractor logic.
- Schedules, schema fields, and dbt grain are not scaffold inputs.
- Simple Entities using a supported response shape are runnable immediately through
  extraction, validation, raw landing, events, and Prefect deployment plumbing.
- Generated validation starts with a permissive Pydantic payload model that accepts
  provider fields while requiring a JSON object.
- Generated dbt staging compiles and exposes ingestion metadata, but analytical field
  selection, types, tests, and Declared Grain remain required follow-up work before
  production use.
- Entity scaffolding generates a raw dbt source declaration, metadata-only staging SQL,
  minimal model YAML, and the matching Raw Completion Event selector.
- Intermediate and mart models are not generated.
- Generated Source and Entity deployments are manual and unscheduled.
- Scheduling is added only after live validation, with rate limits and operational
  cadence explicitly reviewed.
- Phase 08 has no generic authentication scaffold option.
- New Source output includes a `TODO(scaffold)` in its REST client builder and a
  checklist item to add typed settings plus `.env.*.example` keys when authentication
  is required.
- Scaffolding is transactional: preflight collisions and managed blocks, render all
  output, validate it, then write.
- Any preflight, rendering, or validation failure leaves the repository unchanged.
- After writing, the scaffold runs only targeted fast checks:
  - Ruff format on generated Python files.
  - Ruff check on generated Python files.
  - Generated Source unit tests.
  - `dbt parse`.
- Full mypy, the full unit suite, database tests, live API calls, Prefect registration,
  and deployment remain printed follow-up checks.

## Acceptance Source

Use Alpha Vantage as the first scaffold acceptance Source:

```text
Source: alphavantage
Base URL: https://www.alphavantage.co
Entity: time_series_daily
Path: /query
Function parameter: TIME_SERIES_DAILY
Response shape: object
Symbols: SPCX, AAPL, TSM, NVDA
Output size: compact
```

Free-tier constraints:

- Limit live acceptance work to the documented 25 requests per day.
- Space requests by at least two seconds because the API enforces approximately one
  request per second.
- Use `outputsize=compact`; full history is premium-only.
- Never print or commit the API key.

Observed on 2026-06-24:

- `SPCX` returned 7 daily points.
- `AAPL`, `TSM`, and `NVDA` returned 100 daily points each.
- Immediate consecutive calls returned an HTTP 200 response containing a throttling
  information message instead of time-series data.

Alpha Vantage uses:

- Static parameters: `function=TIME_SERIES_DAILY`, `outputsize=compact`.
- Runtime parameter: `symbol`.
- Acceptance values: `SPCX`, `AAPL`, `TSM`, and `NVDA`.
- A two-second interval between symbol requests.
- Response shape: `keyed_object`.
- Records path: `Time Series (Daily)`.
- Key field: `trading_date`.
- Each output payload includes its runtime `symbol`.
- Identity fields: `symbol`, then `trading_date`.
- Provider-specific implementation adds a typed `ALPHAVANTAGE_API_KEY` setting and
  includes it as the `apikey` request parameter.
- Provider-specific implementation uses a two-second request interval.
- Only the Alpha Vantage key name is added to `.env.*.example`; the value remains
  uncommitted.
- These Alpha Vantage changes do not introduce generic authentication or rate-limit
  frameworks into the scaffold.
- Alpha Vantage extraction fails when an HTTP 200 JSON response contains
  `Error Message`, `Information`, or `Note`.
- HTTP-200 error-envelope detection remains provider-specific because those keys may be
  legitimate data in other APIs.
- Generated tests pass and cover the generic scaffolded behavior.
- Unresolved provider-specific and analytical work is marked with `TODO(scaffold)` and
  printed as a post-generation checklist.
- The scaffold does not generate intentionally failing tests.
- If the Source feature folder already exists, the `source` command exits without
  changing files and directs the contributor to the `entity` command.
- The scaffold has no `--force` mode.
- Any target-file or registry collision fails before writing files; contributor code is
  never overwritten.
- Runtime source registration remains explicit.
- The scaffold updates the top-level CLI router and Prefect orchestrator with explicit
  imports and calls.
- Phase 08 does not add dynamic module or plugin discovery.
- Existing Python and YAML registries use clearly delimited scaffold-managed blocks.
- The scaffold parses and replaces only managed blocks.
- Phase 08 does not use AST rewriting or broad position-based text insertion.
- Use the Python standard library unless the existing project dependencies clearly
  provide a simpler option.
- Generate explicit source-owned code that contributors can read and edit.
- Do not introduce a runtime plugin framework solely to support scaffolding.
- Do not overwrite existing files silently.
- Do not infer production schedules, credentials, payload schemas, identity, or dbt
  grains without explicit input.
- Keep generated output compatible with the current feature-folder architecture.
- Support the currently proven REST source pattern only.

## Acceptance Criteria

- One command scaffolds a new Source into a testable, clearly incomplete starting point.
- One command scaffolds a new Entity in an existing supported Source.
- Running either command twice does not overwrite contributor work.
- Generated Python passes Ruff formatting and basic import checks.
- Generated tests identify the provider-specific decisions still requiring
  implementation.
- The command prints the exact next steps for schema, identity, dbt grain, schedule,
  credentials, live testing, and Prefect re-registration.
- Existing CoinGecko and CSV behavior remains unchanged.

## Out of Scope

- Generating correct provider-specific extraction logic from an API URL alone.
- Inferring Pydantic schemas from one live response.
- Inferring dbt types or declared grain automatically.
- Modifying production environment files.
- Automatically deploying or running generated pipelines in production.
- A general plugin system or dynamic source discovery framework unless justified by a
  concrete limitation in the current architecture.

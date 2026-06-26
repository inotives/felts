# Felts Architecture

```mermaid
graph TB
    subgraph External["External Sources"]
        CG["CoinGecko API"]
        CSV["CSV Files"]
        AV["AlphaVantage API"]
    end

    subgraph CLI["CLI Layer"]
        FELTS["felts CLI"]
        CG_CLI["coingecko<br/>run, smoke"]
        CSV_CLI["csv<br/>import"]
        AV_CLI["alphavantage<br/>(planned)"]
    end

    subgraph Extract["Extract Layer"]
        REST_EXT["REST Extractor<br/>(httpx)"]
        CSV_EXT["CSV Extractor<br/>(pandas)"]
        ER["ExtractedRecord"]
    end

    subgraph Write["Write Layer"]
        SR["Schema Registry<br/>(Pydantic models)"]
        RW["RawWriter"]
        RR["RawRecord<br/>+ batch_id + timestamps<br/>+ validation state"]
    end

    subgraph Load["Load Layer"]
        LOADER["BaseLoader<br/>(Postgres)"]
        BATCH["Batch<br/>(traceable group)"]
    end

    subgraph DB["Postgres / TimescaleDB"]
        RAW[("Raw Schema<br/>raw_<entity> tables")]
        COINGECKO_SCH["coingecko schema"]
        CSV_SCH["csv_import schema"]
        AV_SCH["alphavantage schema"]
    end

    subgraph Orchestrate["Orchestration"]
        PREFECT["Prefect Server<br/>(UI :4200)"]
        WORKER["Prefect Worker<br/>(process pool)"]
        EVENTS["Raw Completion<br/>Event"]
        DEPLOY["Deployments<br/>(scheduled + event-triggered)"]
    end

    subgraph Transform["dbt Transform"]
        STAGING["Staging Models<br/>(views)"]
        MARTS["Mart Models<br/>(tables)"]
        DBT_TEST["dbt Tests"]
    end

    subgraph Consume["Consumption"]
        SQL["SQL Queries"]
    end

    subgraph Config["Configuration"]
        CFG["config.yaml"]
        SETTINGS["settings/.env.<br/>local, dev, prod"]
        CONTRACTS["contracts.yaml<br/>(CSV schemas)"]
    end

    %% CLI routing
    FELTS --> CG_CLI
    FELTS --> CSV_CLI
    FELTS --> AV_CLI

    %% Extract
    CG --> REST_EXT
    CSV --> CSV_EXT
    AV --> REST_EXT
    REST_EXT --> ER
    CSV_EXT --> ER

    %% Write
    ER --> SR
    SR --> RW
    RW --> RR
    RR --> LOADER
    LOADER --> BATCH

    %% Load to Postgres
    LOADER --> RAW
    RAW --> COINGECKO_SCH
    RAW --> CSV_SCH
    RAW --> AV_SCH

    %% Orchestration triggers
    PREFECT --> WORKER
    PREFECT --> DEPLOY
    DEPLOY --> EVENTS
    EVENTS -->|"event trigger"| PREFECT

    %% Source flows via Prefect
    CG_CLI -->|"@flow"| PREFECT
    CSV_CLI -->|"@flow"| PREFECT

    %% dbt Transform chain
    EVENTS -->|"selector"| STAGING
    RAW --> STAGING
    STAGING --> MARTS
    STAGING --> DBT_TEST
    MARTS --> DBT_TEST

    %% Consumption
    MARTS --> SQL

    %% Config
    CFG --> PREFECT
    SETTINGS --> PREFECT
    SETTINGS --> LOADER
    CONTRACTS --> CSV_EXT

    %% Styling
    classDef external fill:#e1f5fe,stroke:#0288d1
    classDef cli fill:#f3e5f5,stroke:#7b1fa2
    classDef extract fill:#e8f5e9,stroke:#388e3c
    classDef write fill:#fff3e0,stroke:#f57c00
    classDef db fill:#fce4ec,stroke:#c62828
    classDef orchestrate fill:#f5f5f5,stroke:#616161
    classDef transform fill:#ede7f6,stroke:#512da8
    classDef config fill:#fffde7,stroke:#f9a825

    class CG,CSV,AV external
    class FELTS,CG_CLI,CSV_CLI,AV_CLI cli
    class REST_EXT,CSV_EXT,ER extract
    class SR,RW,RR write
    class LOADER,BATCH write
    class RAW,COINGECKO_SCH,CSV_SCH,AV_SCH db
    class PREFECT,WORKER,EVENTS,DEPLOY orchestrate
    class STAGING,MARTS,DBT_TEST transform
    class CFG,SETTINGS,CONTRACTS config
```

## Pipeline Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as felts CLI
    participant Ext as Extractor
    participant SR as Schema Registry
    participant RW as RawWriter
    participant PG as Postgres
    participant PF as Prefect
    participant dbt as dbt

    User->>CLI: felts coingecko run
    CLI->>Ext: extract(entities)
    Ext->>Ext: fetch from API/CSV
    Ext-->>RW: ExtractedRecord[]

    loop Each batch (1000 records)
        RW->>SR: validate(source, entity)
        SR-->>RW: RegisteredSchema or None
        RW->>RW: wrap as RawRecord<br/>+ batch_id + timestamps
        RW->>PG: INSERT raw_<entity>
    end

    PG-->>RW: WriteResult
    RW-->>CLI: SourceRunSummary

    CLI->>PF: emit Raw Completion Event
    PF->>PF: check automation triggers
    PF->>dbt: deploy dbt-transform flow
    dbt->>PG: dbt run --select <selector>
    PG-->>dbt: staging views + mart tables
    dbt->>PG: dbt test
```

## Layer Responsibilities

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **CLI** | Route commands to source runners | `src/felts/cli.py` |
| **Extract** | Fetch data from APIs/CSV, emit `ExtractedRecord` | `core/extractors/`, `sources/*/extractor.py` |
| **Schema Registry** | Validate payloads against Pydantic models | `core/schemas/registry.py` |
| **RawWriter** | Wrap `ExtractedRecord` → `RawRecord`, assign batch IDs | `core/loaders/writer.py` |
| **Loader** | Persist `RawRecords` to Postgres | `core/loaders/postgres.py` |
| **Orchestration** | Schedule runs, emit events, trigger transforms | `schedules/orchestrator.py`, `sources/*/automations.py` |
| **dbt Transform** | Staging (views) → Marts (tables) | `transforms/models/` |
| **Config** | Settings precedence: explicit > env > .env.<env> > config.yaml | `config/settings.py`, `config.yaml`, `settings/` |

## Settings Precedence

```mermaid
graph LR
    A["explicit values"] --> B["process env"]
    B --> C["settings/.env.FELTS_ENV"]
    C --> D["config.yaml"]
    D --> E["file secrets"]

    style A fill:#c8e6c9
    style E fill:#ffcdd2
```

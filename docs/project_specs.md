# Felts Project Specifications

**Version:** 1.0.0
**Last Updated:** 2024-01-15
**Status:** Draft — In Discussion

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Choices](#2-technology-choices)
3. [Full Project Structure](#3-full-project-structure)
4. [Core Layer](#4-core-layer)
5. [Sources Layer](#5-sources-layer)
6. [Flows Layer](#6-flows-layer)
7. [Schedules Layer](#7-schedules-layer)
8. [Transforms Layer](#8-transforms-layer)
9. [Config Layer](#9-config-layer)
10. [Data Flow Architecture](#10-data-flow-architecture)
11. [Open Discussion Points](#11-open-discussion-points)

---

## 1. Project Overview

Felts, short for Financial ELT Stacks, is a modular, scalable ELT data pipeline for financial data. It ingests data from multiple sources, lands raw data into a warehouse, and transforms it into consumer-ready mart models using dbt.

### Design Philosophy

- **ELT, not ETL** — extract and load raw data first, transform inside the warehouse using dbt. Raw data is always preserved.
- **Feature-based structure** — each data source is fully self-contained in its own folder. Adding a new source requires zero changes to existing code.
- **Event-driven orchestration** — downstream dbt transformations only fire when upstream EL succeeds and new data is detected. No wasted compute.
- **Target-agnostic loading** — swap warehouse targets (Postgres → BigQuery → Snowflake → ClickHouse) via a single env var. No code changes.

### Data Layer Naming Convention

| Layer | Schema Name | Purpose |
|---|---|---|
| Landing | `raw` | Exact API response, JSONB, never modified |
| Clean | `staging` | Unpacked, typed, one model per source entity |
| Enriched | `intermediary` | Cross-source joins, business logic |
| Final | `mart` | Consumer-facing aggregated models |

---

## 2. Technology Choices

### Orchestration — Prefect 3.x (over Luigi / Airflow)

**Luigi** was rejected because:
- No native async support
- Clunky Central Scheduler daemon
- Poor observability and UI
- No event-driven triggers

**Airflow** was considered but rejected because:
- Heavy infrastructure footprint
- Complex DAG definitions
- No native event-driven automations

**Prefect 3.x** was chosen because:
- Native async and concurrent task execution
- Built-in scheduler (cron, interval, event-driven)
- First-class retry logic, caching, state management
- Clean UI dashboard out of the box
- Deployments support cron schedules and event triggers
- `prefect-dbt` integration for transformation layer
- Automations API enables event-driven DAG chaining

### Key Libraries

| Layer | Library | Reason |
|---|---|---|
| REST extraction | `httpx` | Async-first HTTP client |
| WebSocket | `websockets` + `asyncio` | Native async stream handling |
| CSV / files | `polars` | Fast, memory-efficient |
| GraphQL | `httpx` + custom | Lightweight, no heavy client needed |
| Kafka/streams | `confluent-kafka` | Production-grade Kafka client |
| Data validation | `pydantic` v2 | Schema enforcement, coercion |
| DB — Postgres | `asyncpg` | Async native Postgres driver |
| DB — BigQuery | `google-cloud-bigquery` | Official GCP client |
| DB — Snowflake | `snowflake-connector-python` | Official Snowflake client |
| DB — ClickHouse | `clickhouse-connect` | Official ClickHouse HTTP client |
| Orchestration | `prefect` 3.x | See above |
| dbt integration | `prefect-dbt` + `dbt-core` | Managed dbt runs inside Prefect |
| Config | `pydantic-settings` | Typed env var management |

---

## 3. Full Project Structure

```
pipeline/
├── sources/                          # Feature-based: one folder per data source
│   ├── coingecko/
│   │   ├── __init__.py               # Self-registers schemas, exports extractor+loader
│   │   ├── extractor.py              # CoinGecko-specific extraction logic
│   │   ├── loader.py                 # CoinGecko loader config + get_writer()
│   │   ├── schemas/
│   │   │   ├── coins_markets.py      # Pydantic model for /coins/markets
│   │   │   ├── coins_list.py         # Pydantic model for /coins/list
│   │   │   └── global_.py            # Pydantic model for /global
│   │   └── tests/
│   │       ├── test_extractor.py
│   │       └── test_loader.py
│   │
│   ├── coinmarketcap/
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── loader.py
│   │   ├── schemas/
│   │   │   ├── listings_latest.py
│   │   │   └── quotes_latest.py
│   │   └── tests/
│   │
│   ├── defillama/
│   │   ├── __init__.py
│   │   ├── extractor.py              # GraphQL extractor
│   │   ├── loader.py
│   │   ├── schemas/
│   │   │   └── protocols.py
│   │   └── tests/
│   │
│   └── csv_import/
│       ├── __init__.py
│       ├── extractor.py              # CSV file extractor
│       ├── loader.py
│       ├── schemas/
│       │   └── import_record.py
│       └── tests/
│
├── core/                             # Shared transport layer — zero source knowledge
│   ├── extractors/
│   │   ├── base_extractor.py         # Abstract base + ExtractorConfig + ExtractedRecord
│   │   ├── rest_extractor.py         # HTTP client, auth, retry, pagination strategies
│   │   ├── graphql_extractor.py      # GraphQL client, cursor pagination
│   │   ├── csv_extractor.py          # File reader, batch chunking
│   │   └── stream_extractor.py       # WebSocket / Kafka consumer
│   ├── loaders/
│   │   ├── base_loader.py            # Abstract base + LoaderConfig
│   │   ├── postgres_loader.py        # asyncpg implementation
│   │   ├── bigquery_loader.py        # google-cloud-bigquery implementation
│   │   ├── snowflake_loader.py       # snowflake-connector implementation
│   │   ├── clickhouse_loader.py      # clickhouse-connect implementation
│   │   ├── factory.py                # target name → correct loader class
│   │   └── writer.py                 # validation + RawRecord wrapping before load
│   └── schemas/
│       ├── raw_record.py             # Universal raw storage model (all sources)
│       └── registry.py               # source+entity → Pydantic model map
│
├── flows/                            # Prefect flows — thin wiring of extract → load
│   ├── sources/
│   │   ├── coingecko_flow.py
│   │   ├── coinmarketcap_flow.py
│   │   ├── defillama_flow.py
│   │   └── csv_import_flow.py
│   ├── transform_flow.py             # Scoped dbt runs per layer/tag
│   └── master_flow.py                # Runs all EL flows then triggers dbt
│
├── schedules/                        # Feature-based: one folder per source
│   ├── coingecko/
│   │   ├── __init__.py
│   │   ├── events.py                 # Coingecko event name constants
│   │   ├── deployments.py            # Cron schedules + dbt deployments
│   │   └── automations.py            # Event → flow trigger chains
│   ├── coinmarketcap/
│   │   ├── events.py
│   │   ├── deployments.py
│   │   └── automations.py
│   ├── defillama/
│   │   ├── events.py
│   │   ├── deployments.py
│   │   └── automations.py
│   ├── shared/
│   │   ├── base_deployment.py        # Reusable deployment builder helper
│   │   ├── base_automation.py        # Reusable automation builder helper
│   │   └── global_events.py          # Cross-source events
│   └── orchestrator.py               # Single entry point — registers all sources
│
├── transforms/                       # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── packages.yml
│   ├── models/
│   │   ├── raw/                      # Views over loader tables, expose to dbt lineage
│   │   ├── staging/                  # Unpack JSONB → typed columns, per source entity
│   │   │   ├── coingecko/
│   │   │   ├── coinmarketcap/
│   │   │   └── defillama/
│   │   ├── intermediary/             # Cross-source joins, enrichment, business logic
│   │   └── mart/                     # Final consumer models
│   │       ├── finance/
│   │       └── defi/
│   ├── tests/
│   └── macros/
│       ├── generate_schema_name.sql
│       └── safe_cast.sql
│
├── config/
│   └── settings.py                   # Pydantic BaseSettings — all env vars typed
│
└── tests/                            # Top-level integration tests
    ├── test_pipeline_integration.py
    └── conftest.py
```

---

## 4. Core Layer

The core layer owns transport mechanics only. It has no knowledge of any specific data source.

### 4.1 Base Extractor

```python
# core/extractors/base_extractor.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator

@dataclass
class ExtractorConfig:
    source_name:            str
    api_key:                str | None = None
    base_url:               str | None = None
    rate_limit_per_minute:  int = 60
    max_retries:            int = 3
    timeout_seconds:        int = 30
    extra:                  dict = field(default_factory=dict)

@dataclass
class ExtractedRecord:
    source:     str
    entity:     str
    data:       list[dict]
    metadata:   dict = field(default_factory=dict)

class BaseExtractor(ABC):
    def __init__(self, config: ExtractorConfig):
        self.config = config

    @abstractmethod
    async def extract(self, entity: str, params: dict = {}) -> AsyncIterator[ExtractedRecord]:
        """Yield batches of records. Always async generator."""
        ...

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Health check — called before flow starts."""
        ...

    @abstractmethod
    def get_supported_entities(self) -> list[str]:
        """Declarative list of what this source can extract."""
        ...
```

### 4.2 REST Extractor — Pagination Strategies

The REST base class owns all HTTP mechanics. Source plugins pick which pagination strategy to use.

```python
# core/extractors/rest_extractor.py
import httpx, asyncio
from typing import AsyncIterator
from .base_extractor import BaseExtractor, ExtractorConfig, ExtractedRecord

class RestExtractor(BaseExtractor):
    """
    Handles: auth injection, rate limiting, retries,
             cursor / offset / page-token pagination styles.
    Source plugins define WHAT to call, not HOW.
    """

    def __init__(self, config: ExtractorConfig):
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        self._semaphore = asyncio.Semaphore(
            self.config.rate_limit_per_minute // 10
        )

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            headers=self._default_headers(),
        )
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()

    # Override points for source plugins
    def _default_headers(self) -> dict:
        return {}

    def _apply_auth(self, params: dict) -> dict:
        return params

    def _health_endpoint(self) -> str:
        return "/"

    # Pagination strategy 1: offset-based
    async def _paginate_offset(
        self, endpoint: str, params: dict,
        page_size: int, data_key: str,
    ) -> AsyncIterator[list[dict]]:
        offset = 0
        while True:
            resp = await self._get(endpoint, {**params, "limit": page_size, "start": offset})
            records = resp if isinstance(resp, list) else resp.get(data_key, [])
            if not records:
                break
            yield records
            if len(records) < page_size:
                break
            offset += page_size

    # Pagination strategy 2: cursor-based
    async def _paginate_cursor(
        self, endpoint: str, params: dict,
        data_key: str, cursor_key: str = "next_cursor",
    ) -> AsyncIterator[list[dict]]:
        cursor = None
        while True:
            p = {**params, **({"cursor": cursor} if cursor else {})}
            resp = await self._get(endpoint, p)
            records = resp.get(data_key, [])
            if not records:
                break
            yield records
            cursor = resp.get(cursor_key)
            if not cursor:
                break

    # Pagination strategy 3: page token
    async def _paginate_page_token(
        self, endpoint: str, params: dict,
        data_key: str, token_key: str = "nextPageToken",
    ) -> AsyncIterator[list[dict]]:
        token = None
        while True:
            p = {**params, **({"pageToken": token} if token else {})}
            resp = await self._get(endpoint, p)
            records = resp.get(data_key, [])
            yield records
            token = resp.get(token_key)
            if not token:
                break

    # Core HTTP with retry + rate limiting
    async def _get(self, endpoint: str, params: dict = {}) -> dict | list:
        params = self._apply_auth(params)
        for attempt in range(self.config.max_retries):
            async with self._semaphore:
                try:
                    r = await self._client.get(endpoint, params=params)
                    if r.status_code == 429:
                        retry_after = int(r.headers.get("Retry-After", 60))
                        await asyncio.sleep(retry_after)
                        continue
                    r.raise_for_status()
                    return r.json()
                except httpx.HTTPStatusError:
                    if attempt == self.config.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
        raise RuntimeError(f"Failed after {self.config.max_retries} attempts")
```

### 4.3 Base Loader

```python
# core/loaders/base_loader.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.extractors.base_extractor import ExtractedRecord

@dataclass
class LoaderConfig:
    target:         str             # "postgres" | "bigquery" | "snowflake" | "clickhouse"
    schema:         str = "raw"
    batch_size:     int = 1000
    on_conflict:    str = "upsert"  # upsert | append | replace

class BaseLoader(ABC):

    def __init__(self, config: LoaderConfig):
        self.config = config

    @abstractmethod
    async def insert_batch(self, table: str, rows: list[dict]) -> int:
        """Write a batch of RawRecord dicts. Returns rows written."""
        ...

    @abstractmethod
    async def table_exists(self, schema: str, table: str) -> bool:
        ...

    @abstractmethod
    async def create_raw_table(self, schema: str, table: str) -> None:
        """Create raw landing table if not exists. Schema is always identical."""
        ...

    @abstractmethod
    async def validate_connection(self) -> bool:
        ...

    def table_name(self, source: str, entity: str) -> str:
        return f"{source}__{entity}"    # e.g. coingecko__coins_markets
```

### 4.4 Writer — Validation Bridge

The writer sits between flows and loaders. It validates records, wraps them into `RawRecord`, then hands off to the loader. This logic runs once here — never duplicated in loaders.

```python
# core/loaders/writer.py
import uuid
from datetime import datetime, timezone
from core.extractors.base_extractor import ExtractedRecord
from core.schemas.raw_record import RawRecord
from core.schemas.registry import registry
from core.loaders.base_loader import BaseLoader

class DataWriter:
    def __init__(self, loader: BaseLoader):
        self.loader = loader

    async def write(self, record: ExtractedRecord) -> tuple[int, int]:
        """Returns (total_rows_written, new_rows)."""
        table = self.loader.table_name(record.source, record.entity)
        schema = self.loader.config.schema

        if not await self.loader.table_exists(schema, table):
            await self.loader.create_raw_table(schema, table)

        raw_records = self._to_raw_records(record)

        total, new = 0, 0
        for batch in self._chunk(raw_records, self.loader.config.batch_size):
            rows = [r.model_dump() for r in batch]
            written = await self.loader.insert_batch(table, rows)
            total += written
            new   += sum(1 for r in batch if r.is_valid)

        return total, new

    def _to_raw_records(self, record: ExtractedRecord) -> list[RawRecord]:
        batch_id = str(uuid.uuid4())
        rows = []
        for raw in record.data:
            _, errors = registry.validate(record.source, record.entity, raw)
            rows.append(RawRecord(
                id=                 str(uuid.uuid4()),
                source=             record.source,
                entity=             record.entity,
                raw_data=           raw,
                is_valid=           len(errors) == 0,
                validation_errors=  errors,
                schema_version=     "1.0",
                loaded_at=          datetime.now(timezone.utc),
                batch_id=           batch_id,
            ))
        return rows

    def _chunk(self, lst: list, size: int):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]
```

### 4.5 Loader Factory

```python
# core/loaders/factory.py
from core.loaders.base_loader import BaseLoader, LoaderConfig
from config.settings import settings

def get_loader(config: LoaderConfig) -> BaseLoader:
    match config.target:
        case "postgres":
            from core.loaders.postgres_loader import PostgresLoader
            return PostgresLoader(config, dsn=settings.postgres_dsn)
        case "bigquery":
            from core.loaders.bigquery_loader import BigQueryLoader
            return BigQueryLoader(config, project=settings.bq_project)
        case "snowflake":
            from core.loaders.snowflake_loader import SnowflakeLoader
            return SnowflakeLoader(config,
                account=settings.snowflake_account,
                user=settings.snowflake_user,
                password=settings.snowflake_password,
                database=settings.snowflake_database,
                warehouse=settings.snowflake_warehouse,
            )
        case "clickhouse":
            from core.loaders.clickhouse_loader import ClickHouseLoader
            return ClickHouseLoader(config,
                host=settings.clickhouse_host,
                port=settings.clickhouse_port,
            )
        case _:
            raise ValueError(f"Unknown target: {config.target}")
```

### 4.6 Raw Record Schema

```python
# core/schemas/raw_record.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

class RawRecord(BaseModel):
    """Universal storage schema for ALL raw tables across all sources."""
    id:                     str = Field(default_factory=lambda: str(uuid4()))
    source:                 str                 # "coingecko"
    entity:                 str                 # "coins_markets"
    raw_data:               dict                # original API response, untouched
    is_valid:               bool = True         # False if Pydantic validation failed
    validation_errors:      list[str] = []      # field-level errors if is_valid=False
    schema_version:         str = "1.0"         # bump when source schema changes
    loaded_at:              datetime = Field(default_factory=lambda: datetime.utcnow())
    batch_id:               str = ""            # ties all records from one flow run
```

### 4.7 Schema Registry

```python
# core/schemas/registry.py
from pydantic import BaseModel
from typing import Type

class SchemaRegistry:
    def __init__(self):
        self._registry: dict[str, dict[str, Type[BaseModel]]] = {}

    def register(self, source: str, entity: str, schema: Type[BaseModel]):
        self._registry.setdefault(source, {})[entity] = schema

    def get(self, source: str, entity: str) -> Type[BaseModel] | None:
        return self._registry.get(source, {}).get(entity)

    def validate(self, source: str, entity: str, raw: dict) -> tuple[BaseModel | None, list[str]]:
        schema = self.get(source, entity)
        if not schema:
            return None, []     # no schema = passthrough with warning
        try:
            return schema(**raw), []
        except Exception as e:
            errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
            return None, errors

registry = SchemaRegistry()     # singleton imported everywhere
```

### 4.8 Loader Implementations

#### Postgres

```python
# core/loaders/postgres_loader.py
import asyncpg, json
from .base_loader import BaseLoader, LoaderConfig

class PostgresLoader(BaseLoader):

    def __init__(self, config: LoaderConfig, dsn: str):
        super().__init__(config)
        self.dsn = dsn
        self._pool = None

    async def _pool_(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(self.dsn)
        return self._pool

    async def validate_connection(self) -> bool:
        try:
            pool = await self._pool_()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def table_exists(self, schema: str, table: str) -> bool:
        pool = await self._pool_()
        async with pool.acquire() as conn:
            return await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = $1 AND table_name = $2
                )
            """, schema, table)

    async def create_raw_table(self, schema: str, table: str) -> None:
        pool = await self._pool_()
        async with pool.acquire() as conn:
            await conn.execute(f"""
                CREATE SCHEMA IF NOT EXISTS {schema};
                CREATE TABLE IF NOT EXISTS {schema}.{table} (
                    id                  TEXT PRIMARY KEY,
                    source              TEXT NOT NULL,
                    entity              TEXT NOT NULL,
                    raw_data            JSONB NOT NULL,
                    is_valid            BOOLEAN DEFAULT TRUE,
                    validation_errors   JSONB DEFAULT '[]',
                    schema_version      TEXT DEFAULT '1.0',
                    loaded_at           TIMESTAMPTZ DEFAULT NOW(),
                    batch_id            TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_{table}_loaded_at
                    ON {schema}.{table} (loaded_at);
                CREATE INDEX IF NOT EXISTS idx_{table}_is_valid
                    ON {schema}.{table} (is_valid);
            """)

    async def insert_batch(self, table: str, rows: list[dict]) -> int:
        pool = await self._pool_()
        full_table = f"{self.config.schema}.{table}"
        async with pool.acquire() as conn:
            await conn.executemany(f"""
                INSERT INTO {full_table}
                    (id, source, entity, raw_data, is_valid,
                     validation_errors, schema_version, loaded_at, batch_id)
                VALUES ($1,$2,$3,$4::jsonb,$5,$6::jsonb,$7,$8,$9)
                ON CONFLICT (id) DO UPDATE
                    SET raw_data = EXCLUDED.raw_data,
                        loaded_at = EXCLUDED.loaded_at
            """, [self._row_to_tuple(r) for r in rows])
        return len(rows)

    def _row_to_tuple(self, r: dict) -> tuple:
        return (
            r["id"], r["source"], r["entity"],
            json.dumps(r["raw_data"]), r["is_valid"],
            json.dumps(r["validation_errors"]),
            r["schema_version"], r["loaded_at"], r["batch_id"],
        )
```

#### BigQuery

```python
# core/loaders/bigquery_loader.py
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from .base_loader import BaseLoader, LoaderConfig
import json

class BigQueryLoader(BaseLoader):

    def __init__(self, config: LoaderConfig, project: str, dataset: str = None):
        super().__init__(config)
        self.project = project
        self.dataset = dataset or config.schema
        self.client = bigquery.Client(project=project)

    async def validate_connection(self) -> bool:
        try:
            list(self.client.list_datasets(max_results=1))
            return True
        except Exception:
            return False

    async def table_exists(self, schema: str, table: str) -> bool:
        try:
            self.client.get_table(f"{self.project}.{schema}.{table}")
            return True
        except NotFound:
            return False

    async def create_raw_table(self, schema: str, table: str) -> None:
        dataset_ref = self.client.dataset(schema)
        try:
            self.client.get_dataset(dataset_ref)
        except NotFound:
            self.client.create_dataset(bigquery.Dataset(dataset_ref))

        bq_schema = [
            bigquery.SchemaField("id",                "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("source",            "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("entity",            "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("raw_data",          "JSON",      mode="REQUIRED"),
            bigquery.SchemaField("is_valid",          "BOOLEAN"),
            bigquery.SchemaField("validation_errors", "JSON"),
            bigquery.SchemaField("schema_version",    "STRING"),
            bigquery.SchemaField("loaded_at",         "TIMESTAMP"),
            bigquery.SchemaField("batch_id",          "STRING"),
        ]
        self.client.create_table(
            bigquery.Table(f"{self.project}.{schema}.{table}", schema=bq_schema),
            exists_ok=True
        )

    async def insert_batch(self, table: str, rows: list[dict]) -> int:
        table_ref = f"{self.project}.{self.dataset}.{table}"
        bq_rows = [
            {**r,
             "raw_data": json.dumps(r["raw_data"]),
             "validation_errors": json.dumps(r["validation_errors"]),
             "loaded_at": r["loaded_at"].isoformat()}
            for r in rows
        ]
        errors = self.client.insert_rows_json(table_ref, bq_rows)
        if errors:
            raise RuntimeError(f"BigQuery insert errors: {errors}")
        return len(rows)
```

#### Snowflake

```python
# core/loaders/snowflake_loader.py
import snowflake.connector, json
from .base_loader import BaseLoader, LoaderConfig

class SnowflakeLoader(BaseLoader):

    def __init__(self, config: LoaderConfig, account: str, user: str,
                 password: str, database: str, warehouse: str):
        super().__init__(config)
        self._conn_params = dict(
            account=account, user=user, password=password,
            database=database, warehouse=warehouse,
        )

    def _conn(self):
        return snowflake.connector.connect(**self._conn_params)

    async def validate_connection(self) -> bool:
        try:
            with self._conn() as conn:
                conn.cursor().execute("SELECT 1")
            return True
        except Exception:
            return False

    async def table_exists(self, schema: str, table: str) -> bool:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = '{schema.upper()}'
                AND table_name = '{table.upper()}'
            """)
            return cur.fetchone()[0] > 0

    async def create_raw_table(self, schema: str, table: str) -> None:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema}.{table} (
                    id                  VARCHAR PRIMARY KEY,
                    source              VARCHAR NOT NULL,
                    entity              VARCHAR NOT NULL,
                    raw_data            VARIANT NOT NULL,
                    is_valid            BOOLEAN DEFAULT TRUE,
                    validation_errors   VARIANT DEFAULT '[]',
                    schema_version      VARCHAR DEFAULT '1.0',
                    loaded_at           TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
                    batch_id            VARCHAR
                )
            """)

    async def insert_batch(self, table: str, rows: list[dict]) -> int:
        schema = self.config.schema
        with self._conn() as conn:
            cur = conn.cursor()
            cur.executemany(f"""
                INSERT INTO {schema}.{table}
                    (id, source, entity, raw_data, is_valid,
                     validation_errors, schema_version, loaded_at, batch_id)
                VALUES (%s,%s,%s,PARSE_JSON(%s),%s,PARSE_JSON(%s),%s,%s,%s)
            """, [
                (r["id"], r["source"], r["entity"],
                 json.dumps(r["raw_data"]), r["is_valid"],
                 json.dumps(r["validation_errors"]),
                 r["schema_version"], r["loaded_at"], r["batch_id"])
                for r in rows
            ])
        return len(rows)
```

#### ClickHouse

```python
# core/loaders/clickhouse_loader.py
import clickhouse_connect, json
from .base_loader import BaseLoader, LoaderConfig

class ClickHouseLoader(BaseLoader):

    def __init__(self, config: LoaderConfig, host: str, port: int = 8123,
                 user: str = "default", password: str = ""):
        super().__init__(config)
        self.client = clickhouse_connect.get_client(
            host=host, port=port, user=user, password=password
        )

    async def validate_connection(self) -> bool:
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    async def table_exists(self, schema: str, table: str) -> bool:
        result = self.client.query(f"""
            SELECT COUNT(*) FROM system.tables
            WHERE database = '{schema}' AND name = '{table}'
        """)
        return result.first_row[0] > 0

    async def create_raw_table(self, schema: str, table: str) -> None:
        self.client.command(f"CREATE DATABASE IF NOT EXISTS {schema}")
        self.client.command(f"""
            CREATE TABLE IF NOT EXISTS {schema}.{table} (
                id                  String,
                source              String,
                entity              String,
                raw_data            String,
                is_valid            UInt8,
                validation_errors   String,
                schema_version      String,
                loaded_at           DateTime64(3, 'UTC'),
                batch_id            String
            )
            ENGINE = MergeTree()
            ORDER BY (source, entity, loaded_at)
            PARTITION BY toYYYYMM(loaded_at)
        """)

    async def insert_batch(self, table: str, rows: list[dict]) -> int:
        schema = self.config.schema
        data = [
            [r["id"], r["source"], r["entity"],
             json.dumps(r["raw_data"]), int(r["is_valid"]),
             json.dumps(r["validation_errors"]),
             r["schema_version"], r["loaded_at"], r["batch_id"]]
            for r in rows
        ]
        self.client.insert(
            f"{schema}.{table}", data,
            column_names=["id","source","entity","raw_data","is_valid",
                         "validation_errors","schema_version","loaded_at","batch_id"]
        )
        return len(rows)
```

---

## 5. Sources Layer

Each source folder is entirely self-contained. The `__init__.py` auto-registers schemas on import so flows never need to do manual registration.

### 5.1 CoinGecko

```python
# sources/coingecko/__init__.py
from .extractor import CoinGeckoExtractor
from .loader import get_coingecko_writer
from .schemas.coins_markets import CoinMarket
from .schemas.coins_list import CoinsList
from .schemas.global_ import GlobalMarket
from core.schemas.registry import registry

registry.register("coingecko", "coins_markets", CoinMarket)
registry.register("coingecko", "coins_list",    CoinsList)
registry.register("coingecko", "global",        GlobalMarket)
```

```python
# sources/coingecko/extractor.py
from core.extractors.rest_extractor import RestExtractor
from core.extractors.base_extractor import ExtractorConfig, ExtractedRecord
from typing import AsyncIterator

class CoinGeckoExtractor(RestExtractor):

    def _default_headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.config.api_key:
            headers["x-cg-pro-api-key"] = self.config.api_key
        return headers

    def _health_endpoint(self) -> str:
        return "/api/v3/ping"

    def get_supported_entities(self) -> list[str]:
        return ["coins_list", "coins_markets", "global"]

    async def extract(self, entity: str, params: dict = {}) -> AsyncIterator[ExtractedRecord]:
        async with self:
            match entity:
                case "coins_markets":
                    async for batch in self._paginate_offset(
                        endpoint="/api/v3/coins/markets",
                        params={"vs_currency": "usd", "order": "market_cap_desc", **params},
                        page_size=250,
                        data_key="",
                    ):
                        yield ExtractedRecord(source="coingecko", entity=entity, data=batch)

                case "coins_list":
                    resp = await self._get("/api/v3/coins/list", {"include_platform": "true"})
                    yield ExtractedRecord(source="coingecko", entity=entity, data=resp)

                case "global":
                    resp = await self._get("/api/v3/global")
                    yield ExtractedRecord(source="coingecko", entity=entity, data=[resp["data"]])

                case _:
                    raise ValueError(f"Unsupported entity: {entity}")
```

```python
# sources/coingecko/loader.py
from core.loaders.base_loader import LoaderConfig
from core.loaders.factory import get_loader
from core.loaders.writer import DataWriter
from config.settings import settings

def get_coingecko_writer() -> DataWriter:
    config = LoaderConfig(
        target=settings.default_target,
        schema="raw",
        batch_size=500,
        on_conflict="upsert",
    )
    return DataWriter(loader=get_loader(config))
```

```python
# sources/coingecko/schemas/coins_markets.py
from pydantic import BaseModel, field_validator
from decimal import Decimal
from datetime import datetime

class CoinMarket(BaseModel):
    """
    Contract for GET /api/v3/coins/markets
    Docs: https://docs.coingecko.com/reference/coins-markets
    Last verified: 2024-01-15
    """
    id:                             str
    symbol:                         str
    name:                           str
    current_price:                  Decimal | None = None
    market_cap:                     Decimal | None = None
    market_cap_rank:                int | None = None
    total_volume:                   Decimal | None = None
    price_change_percentage_24h:    float | None = None
    circulating_supply:             Decimal | None = None
    total_supply:                   Decimal | None = None
    last_updated:                   datetime | None = None

    @field_validator("current_price", "market_cap", "total_volume", mode="before")
    @classmethod
    def coerce_numeric(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))

    class Config:
        extra = "allow"     # extra API fields captured but don't break validation
```

### 5.2 CoinMarketCap

```python
# sources/coinmarketcap/extractor.py
from core.extractors.rest_extractor import RestExtractor
from core.extractors.base_extractor import ExtractedRecord
from typing import AsyncIterator

class CoinMarketCapExtractor(RestExtractor):

    def _default_headers(self) -> dict:
        return {
            "X-CMC_PRO_API_KEY": self.config.api_key,
            "Accept": "application/json",
        }

    def _health_endpoint(self) -> str:
        return "/v1/key/info"

    def get_supported_entities(self) -> list[str]:
        return ["listings_latest", "quotes_latest"]

    async def extract(self, entity: str, params: dict = {}) -> AsyncIterator[ExtractedRecord]:
        async with self:
            match entity:
                case "listings_latest":
                    async for batch in self._paginate_offset(
                        endpoint="/v1/cryptocurrency/listings/latest",
                        params={"convert": "USD", **params},
                        page_size=5000,
                        data_key="data",
                    ):
                        yield ExtractedRecord(source="coinmarketcap", entity=entity, data=batch)

                case "quotes_latest":
                    ids = params.get("ids", [])
                    for chunk in [ids[i:i+100] for i in range(0, len(ids), 100)]:
                        resp = await self._get(
                            "/v2/cryptocurrency/quotes/latest",
                            {"id": ",".join(map(str, chunk)), "convert": "USD"}
                        )
                        yield ExtractedRecord(
                            source="coinmarketcap", entity=entity,
                            data=list(resp["data"].values())
                        )
```

### 5.3 DeFi Llama (GraphQL)

```python
# sources/defillama/extractor.py
from core.extractors.graphql_extractor import GraphQLExtractor
from core.extractors.base_extractor import ExtractedRecord
from typing import AsyncIterator

class DefiLlamaExtractor(GraphQLExtractor):

    def get_supported_entities(self) -> list[str]:
        return ["protocols", "yields", "tvl_chart"]

    async def extract(self, entity: str, params: dict = {}) -> AsyncIterator[ExtractedRecord]:
        async with self:
            match entity:
                case "protocols":
                    query = """
                        query GetProtocols($limit: Int, $offset: Int) {
                            protocols(limit: $limit, offset: $offset) {
                                id name chain tvl category
                                change_1h change_1d change_7d
                            }
                        }
                    """
                    async for batch in self._paginate_graphql(
                        query=query,
                        variables={"limit": 100},
                        data_key="protocols",
                    ):
                        yield ExtractedRecord(source="defillama", entity=entity, data=batch)
```

### 5.4 CSV Import

```python
# sources/csv_import/extractor.py
from core.extractors.csv_extractor import CsvExtractor
from core.extractors.base_extractor import ExtractedRecord
from typing import AsyncIterator

class CsvImportExtractor(CsvExtractor):

    def get_supported_entities(self) -> list[str]:
        return ["generic_import", "price_history", "custom_assets"]

    async def extract(self, entity: str, params: dict = {}) -> AsyncIterator[ExtractedRecord]:
        file_path = params.get("file_path")
        if not file_path:
            raise ValueError("csv_import requires 'file_path' in params")

        async for batch in self._read_csv_batches(
            file_path=file_path,
            batch_size=self.config.extra.get("batch_size", 1000),
            delimiter=self.config.extra.get("delimiter", ","),
        ):
            yield ExtractedRecord(source="csv_import", entity=entity, data=batch)
```

---

## 6. Flows Layer

Flows are thin wiring only — they connect extractors to loaders and emit events. No business logic lives here.

```python
# flows/sources/coingecko_flow.py
from prefect import flow, task, get_run_logger
from prefect.events import emit_event
from prefect.artifacts import create_table_artifact
from sources.coingecko import CoinGeckoExtractor, get_coingecko_writer
from core.extractors.base_extractor import ExtractorConfig
from schedules.coingecko.events import COINGECKO_EVENTS
from config.settings import settings

@task(retries=3, retry_delay_seconds=60, task_run_name="extract-load-{entity}")
async def extract_and_load(entity: str) -> dict:
    extractor = CoinGeckoExtractor(ExtractorConfig(
        source_name="coingecko",
        api_key=settings.coingecko_api_key,
        base_url="https://api.coingecko.com",
    ))
    writer = get_coingecko_writer()

    total, new = 0, 0
    async for batch in extractor.extract(entity):
        t, n = await writer.write(batch)
        total += t
        new   += n

    return {"entity": entity, "rows_loaded": total, "new_rows": new}


@flow(name="coingecko-get-assets")
async def coingecko_get_assets_flow():
    logger = get_run_logger()
    result = await extract_and_load("coins_list")
    logger.info(f"Loaded {result['rows_loaded']} rows, {result['new_rows']} new")

    event = (COINGECKO_EVENTS.NEW_ASSETS_DETECTED
             if result["new_rows"] > 0
             else COINGECKO_EVENTS.NO_NEW_ASSETS)

    emit_event(
        event=event,
        resource={"prefect.resource.id": "coingecko.assets"},
        payload=result
    )

    emit_event(
        event=COINGECKO_EVENTS.ASSETS_COMPLETED,
        resource={"prefect.resource.id": "coingecko.assets"},
        payload=result
    )

    await create_table_artifact(
        key="coingecko-assets-run-summary",
        table=[result],
        description="CoinGecko get_assets run summary"
    )
```

### dbt Transform Flow

```python
# flows/transform_flow.py
from prefect import flow, task
from prefect.events import emit_event
from prefect_dbt.cli.commands import DbtCoreOperation

@task(task_run_name="dbt-run-{selector}")
async def run_dbt_models(selector: str, full_refresh: bool = False) -> dict:
    cmd = f"dbt run --select {selector}"
    if full_refresh:
        cmd += " --full-refresh"
    result = await DbtCoreOperation(
        commands=[cmd],
        project_dir="transforms/",
        profiles_dir="transforms/",
    ).run_async()
    return {"selector": selector, "success": result.return_code == 0}


@task
async def run_dbt_tests(selector: str) -> dict:
    result = await DbtCoreOperation(
        commands=[f"dbt test --select {selector}"],
        project_dir="transforms/",
        profiles_dir="transforms/",
    ).run_async()
    return {"selector": selector, "passed": result.return_code == 0}


@flow(name="dbt-staging-coingecko-assets")
async def dbt_staging_coingecko_assets_flow(full_refresh: bool = False):
    from schedules.coingecko.events import COINGECKO_EVENTS
    run  = await run_dbt_models("tag:staging_coingecko_assets", full_refresh)
    test = await run_dbt_tests("tag:staging_coingecko_assets")

    if run["success"] and test["passed"]:
        emit_event(
            event=COINGECKO_EVENTS.DBT_STAGING_COMPLETED,
            resource={"prefect.resource.id": "dbt.staging.coingecko"},
        )
    else:
        raise RuntimeError(f"dbt staging failed: {run}, {test}")


@flow(name="dbt-intermediary-coins")
async def dbt_intermediary_coins_flow():
    from schedules.coingecko.events import COINGECKO_EVENTS
    run  = await run_dbt_models("tag:intermediary_coins")
    test = await run_dbt_tests("tag:intermediary_coins")
    if run["success"] and test["passed"]:
        emit_event(
            event=COINGECKO_EVENTS.DBT_INTERMEDIARY_COMPLETED,
            resource={"prefect.resource.id": "dbt.intermediary.coins"},
        )
    else:
        raise RuntimeError("Intermediary coins models failed")


@flow(name="dbt-mart-finance")
async def dbt_mart_finance_flow():
    from schedules.coingecko.events import COINGECKO_EVENTS
    run  = await run_dbt_models("mart/finance")
    test = await run_dbt_tests("mart/finance")
    if run["success"]:
        emit_event(
            event=COINGECKO_EVENTS.DBT_MART_COMPLETED,
            resource={"prefect.resource.id": "dbt.mart.finance"},
        )
```

---

## 7. Schedules Layer

Feature-based scheduling — each source folder owns its events, deployments, and automations.

### 7.1 Events

```python
# schedules/coingecko/events.py
from dataclasses import dataclass

@dataclass(frozen=True)
class CoinGeckoEvents:
    """
    All events owned by the coingecko pipeline feature.
    Convention: {source}.{entity}.{outcome}
    """
    ASSETS_COMPLETED            = "coingecko.assets.completed"
    MARKETS_COMPLETED           = "coingecko.markets.completed"
    GLOBAL_COMPLETED            = "coingecko.global.completed"

    NEW_ASSETS_DETECTED         = "coingecko.assets.new_assets_detected"
    NO_NEW_ASSETS               = "coingecko.assets.no_new_assets"

    DBT_STAGING_COMPLETED       = "coingecko.dbt.staging.completed"
    DBT_INTERMEDIARY_COMPLETED  = "coingecko.dbt.intermediary.completed"
    DBT_MART_COMPLETED          = "coingecko.dbt.mart.completed"

    ASSETS_FAILED               = "coingecko.assets.failed"
    DBT_STAGING_FAILED          = "coingecko.dbt.staging.failed"
    DBT_INTERMEDIARY_FAILED     = "coingecko.dbt.intermediary.failed"

COINGECKO_EVENTS = CoinGeckoEvents()
```

### 7.2 Deployments

```python
# schedules/coingecko/deployments.py
from prefect.server.schemas.schedules import CronSchedule
from flows.sources.coingecko_flow import (
    coingecko_get_assets_flow,
    coingecko_get_markets_flow,
)
from flows.transform_flow import (
    dbt_staging_coingecko_assets_flow,
    dbt_intermediary_coins_flow,
    dbt_mart_finance_flow,
)
from schedules.shared.base_deployment import build_deployment

EL_DEPLOYMENTS = [
    {
        "flow":         coingecko_get_assets_flow,
        "name":         "coingecko-get-assets",
        "description":  "Daily extract of CoinGecko coins list → raw schema",
        "schedules":    [CronSchedule(cron="0 0 * * *", timezone="UTC")],
        "tags":         ["coingecko", "el", "assets"],
    },
    {
        "flow":         coingecko_get_markets_flow,
        "name":         "coingecko-get-markets",
        "description":  "Hourly extract of CoinGecko market data → raw schema",
        "schedules":    [CronSchedule(cron="0 * * * *", timezone="UTC")],
        "tags":         ["coingecko", "el", "markets"],
    },
]

DBT_DEPLOYMENTS = [
    {
        "flow":         dbt_staging_coingecko_assets_flow,
        "name":         "dbt-staging-coingecko-assets",
        "description":  "Staging models for coingecko assets. Event-driven only.",
        "schedules":    [],
        "tags":         ["coingecko", "dbt", "staging"],
        "parameters":   {"full_refresh": False},
    },
    {
        "flow":         dbt_intermediary_coins_flow,
        "name":         "dbt-intermediary-coins",
        "description":  "Intermediary coin enrichment. Triggered by staging.",
        "schedules":    [],
        "tags":         ["coingecko", "dbt", "intermediary"],
    },
    {
        "flow":         dbt_mart_finance_flow,
        "name":         "dbt-mart-finance",
        "description":  "Finance mart models. Triggered by intermediary.",
        "schedules":    [],
        "tags":         ["coingecko", "dbt", "mart"],
    },
]

ALL_DEPLOYMENTS = EL_DEPLOYMENTS + DBT_DEPLOYMENTS

async def register_deployments(env: str = "prod"):
    for config in ALL_DEPLOYMENTS:
        await build_deployment(config, env=env)
        print(f"  ✓ {config['name']}/{env}")
```

### 7.3 Automations

```python
# schedules/coingecko/automations.py
from prefect.automations import Automation
from prefect.events.schemas.automations import EventTrigger, RunDeployment
from .events import COINGECKO_EVENTS

"""
Event chain:
  coingecko-get-assets (cron: daily 00:00)
      │
      ├─ new assets detected
      │       └──▶ dbt-staging-coingecko-assets
      │                   └──▶ dbt-intermediary-coins
      │                               └──▶ dbt-mart-finance
      │
      └─ no new assets → chain stops
"""

AUTOMATIONS = [
    Automation(
        name="coingecko__new-assets__trigger-staging",
        description="New assets detected → refresh staging models",
        trigger=EventTrigger(
            expect={COINGECKO_EVENTS.NEW_ASSETS_DETECTED},
            within=300,
        ),
        actions=[RunDeployment(
            deployment_name="dbt-staging-coingecko-assets/prod",
            parameters={"full_refresh": False},
        )],
    ),
    Automation(
        name="coingecko__staging-done__trigger-intermediary",
        description="Staging complete → run intermediary enrichment",
        trigger=EventTrigger(
            expect={COINGECKO_EVENTS.DBT_STAGING_COMPLETED},
            within=600,
        ),
        actions=[RunDeployment(deployment_name="dbt-intermediary-coins/prod")],
    ),
    Automation(
        name="coingecko__intermediary-done__trigger-mart",
        description="Intermediary complete → run finance mart",
        trigger=EventTrigger(
            expect={COINGECKO_EVENTS.DBT_INTERMEDIARY_COMPLETED},
            within=600,
        ),
        actions=[RunDeployment(deployment_name="dbt-mart-finance/prod")],
    ),
    Automation(
        name="coingecko__any-failure__notify",
        description="Any coingecko failure → send alert",
        trigger=EventTrigger(
            expect={
                COINGECKO_EVENTS.ASSETS_FAILED,
                COINGECKO_EVENTS.DBT_STAGING_FAILED,
                COINGECKO_EVENTS.DBT_INTERMEDIARY_FAILED,
            },
            within=60,
        ),
        actions=[RunDeployment(deployment_name="notify-on-failure/prod")],
    ),
]

def register_automations():
    for automation in AUTOMATIONS:
        automation.save(name=automation.name, overwrite=True)
        print(f"  ✓ automation: {automation.name}")
```

### 7.4 Orchestrator

```python
# schedules/orchestrator.py
import asyncio
from schedules.coingecko.deployments import register_deployments as coingecko_deps
from schedules.coingecko.automations import register_automations as coingecko_autos
from schedules.coinmarketcap.deployments import register_deployments as cmc_deps
from schedules.coinmarketcap.automations import register_automations as cmc_autos
from schedules.defillama.deployments import register_deployments as defillama_deps
from schedules.defillama.automations import register_automations as defillama_autos

SOURCES = [
    ("coingecko",     coingecko_deps,   coingecko_autos),
    ("coinmarketcap", cmc_deps,         cmc_autos),
    ("defillama",     defillama_deps,   defillama_autos),
]

async def bootstrap(env: str = "prod"):
    for source, deps_fn, autos_fn in SOURCES:
        print(f"\n[ {source} ]")
        await deps_fn(env=env)
        autos_fn()
    print("\n✓ All deployments and automations registered.")

if __name__ == "__main__":
    asyncio.run(bootstrap())
```

---

## 8. Transforms Layer

dbt project with four schema layers. All SQL transformation logic lives here exclusively — no transformation in Python.

### 8.1 dbt_project.yml

```yaml
name: felts
version: 1.0.0
profile: felts

model-paths: ["models"]
test-paths: ["tests"]
macro-paths: ["macros"]

models:
  felts:
    raw:
      +schema: raw
      +materialized: view
      +tags: ["raw"]

    staging:
      +schema: staging
      +materialized: view
      +tags: ["staging"]

    intermediary:
      +schema: intermediary
      +materialized: table
      +tags: ["intermediary"]
      +post-hook: "ANALYZE {{ this }}"

    mart:
      +schema: mart
      +materialized: table
      +tags: ["mart"]
      +post-hook: "ANALYZE {{ this }}"
```

### 8.2 Raw Model (View Over Loader Table)

```sql
-- models/raw/raw_coingecko__coins_markets.sql
SELECT
    id, source, entity, raw_data,
    is_valid, validation_errors,
    schema_version, loaded_at, batch_id
FROM {{ source('raw_loader', 'coingecko__coins_markets') }}
```

### 8.3 Staging Model (Unpack + Type)

```sql
-- models/staging/coingecko/stg_coingecko__coins_markets.sql
WITH source AS (
    SELECT * FROM {{ ref('raw_coingecko__coins_markets') }}
    WHERE is_valid = true
),
unpacked AS (
    SELECT
        raw_data->>'id'                             AS coin_id,
        raw_data->>'symbol'                         AS symbol,
        UPPER(raw_data->>'symbol')                  AS symbol_upper,
        raw_data->>'name'                           AS coin_name,
        (raw_data->>'current_price')::NUMERIC       AS current_price_usd,
        (raw_data->>'market_cap')::NUMERIC          AS market_cap_usd,
        (raw_data->>'market_cap_rank')::INT         AS market_cap_rank,
        (raw_data->>'total_volume')::NUMERIC        AS volume_24h_usd,
        (raw_data->>'price_change_percentage_24h')::FLOAT AS price_change_pct_24h,
        (raw_data->>'circulating_supply')::NUMERIC  AS circulating_supply,
        (raw_data->>'total_supply')::NUMERIC        AS total_supply,
        (raw_data->>'last_updated')::TIMESTAMPTZ    AS last_updated_at,
        loaded_at,
        batch_id
    FROM source
),
deduped AS (
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY coin_id, last_updated_at
                ORDER BY loaded_at DESC, batch_id DESC
            ) AS row_num
        FROM unpacked
        WHERE coin_id IS NOT NULL
    ) ranked
    WHERE row_num = 1
)
SELECT
    coin_id,
    symbol,
    symbol_upper,
    coin_name,
    current_price_usd,
    market_cap_usd,
    market_cap_rank,
    volume_24h_usd,
    price_change_pct_24h,
    circulating_supply,
    total_supply,
    last_updated_at,
    loaded_at,
    batch_id
FROM deduped
```

Staging deduplication is written directly in each dbt model using that model's natural key and ordering rules. If the same pattern repeats across many models, this can later be extracted into a shared dbt macro.

### 8.4 Intermediary Model (Cross-source Join)

```sql
-- models/intermediary/int_coins__market_enriched.sql
WITH coingecko AS (
    SELECT * FROM {{ ref('stg_coingecko__coins_markets') }}
),
coinmarketcap AS (
    SELECT * FROM {{ ref('stg_coinmarketcap__listings') }}
),
defillama AS (
    SELECT * FROM {{ ref('stg_defillama__protocols') }}
)
SELECT
    cg.coin_id,
    cg.symbol,
    cg.coin_name,
    cg.current_price_usd,
    cg.market_cap_usd,
    cg.volume_24h_usd,
    cg.price_change_pct_24h,
    cg.circulating_supply,
    cmc.cmc_rank,
    cmc.max_supply,
    dl.tvl_usd              AS defi_tvl_usd,
    dl.category             AS defi_category,
    CASE WHEN cmc.symbol IS NOT NULL THEN true ELSE false END AS has_cmc_data,
    CASE WHEN dl.symbol  IS NOT NULL THEN true ELSE false END AS has_defi_data,
    GREATEST(cg._loaded_at, cmc._loaded_at) AS _updated_at
FROM coingecko cg
LEFT JOIN coinmarketcap cmc USING (symbol)
LEFT JOIN defillama     dl  USING (symbol)
```

### 8.5 Mart Model (Consumer-facing)

```sql
-- models/mart/finance/mart_coins__summary.sql
WITH base AS (
    SELECT * FROM {{ ref('int_coins__market_enriched') }}
)
SELECT
    coin_id, symbol, coin_name,
    current_price_usd, market_cap_usd, volume_24h_usd,
    price_change_pct_24h, cmc_rank, circulating_supply,
    defi_tvl_usd, defi_category,
    ROUND(volume_24h_usd / NULLIF(market_cap_usd, 0), 4)     AS volume_to_mcap_ratio,
    ROUND(market_cap_usd / NULLIF(circulating_supply, 0), 2) AS implied_price_check,
    has_cmc_data, has_defi_data,
    _updated_at
FROM base
WHERE market_cap_usd > 0
  AND current_price_usd > 0
ORDER BY market_cap_usd DESC
```

---

## 9. Config Layer

```python
# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

    # Target warehouse — change this one var to switch all loaders
    default_target: str = Field("postgres", env="DEFAULT_TARGET")

    # Postgres
    postgres_dsn: str = Field("", env="POSTGRES_DSN")

    # BigQuery
    bq_project:  str = Field("", env="BQ_PROJECT")
    bq_dataset:  str = Field("raw", env="BQ_DATASET")

    # Snowflake
    snowflake_account:   str = Field("", env="SNOWFLAKE_ACCOUNT")
    snowflake_user:      str = Field("", env="SNOWFLAKE_USER")
    snowflake_password:  str = Field("", env="SNOWFLAKE_PASSWORD")
    snowflake_database:  str = Field("", env="SNOWFLAKE_DATABASE")
    snowflake_warehouse: str = Field("", env="SNOWFLAKE_WAREHOUSE")

    # ClickHouse
    clickhouse_host:     str = Field("localhost", env="CLICKHOUSE_HOST")
    clickhouse_port:     int = Field(8123,        env="CLICKHOUSE_PORT")
    clickhouse_user:     str = Field("default",   env="CLICKHOUSE_USER")
    clickhouse_password: str = Field("",          env="CLICKHOUSE_PASSWORD")

    # Source API keys
    coingecko_api_key:      str | None = Field(None, env="COINGECKO_API_KEY")
    coinmarketcap_api_key:  str        = Field("",   env="CMC_API_KEY")

    # dbt schema names
    raw_schema:          str = "raw"
    staging_schema:      str = "staging"
    intermediary_schema: str = "intermediary"
    mart_schema:         str = "mart"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 10. Data Flow Architecture

### Full Pipeline Flow

```
00:00 UTC cron trigger
        │
        ▼
coingecko_get_assets_flow
        │
        ├── ExtractorConfig(api_key, base_url)
        │         │
        │         ▼
        │   CoinGeckoExtractor.extract("coins_list")
        │         │  paginate_offset → yield ExtractedRecord batches
        │         ▼
        │   DataWriter.write(batch)
        │         │  validate via SchemaRegistry
        │         │  wrap into RawRecord
        │         │  loader.insert_batch() → raw.coingecko__coins_list
        │         ▼
        │   returns (total_rows, new_rows)
        │
        ├── new_rows > 0?
        │       │ YES → emit: coingecko.assets.new_assets_detected
        │       │ NO  → emit: coingecko.assets.no_new_assets (chain stops)
        │
        ▼  [Prefect Automation fires]
dbt_staging_coingecko_assets_flow
        │  dbt run --select tag:staging_coingecko_assets
        │  dbt test --select tag:staging_coingecko_assets
        │  emit: coingecko.dbt.staging.completed
        │
        ▼  [Prefect Automation fires]
dbt_intermediary_coins_flow
        │  dbt run --select tag:intermediary_coins
        │  emit: coingecko.dbt.intermediary.completed
        │
        ▼  [Prefect Automation fires]
dbt_mart_finance_flow
           dbt run --select mart/finance
           emit: coingecko.dbt.mart.completed
```

### Raw Table Structure (All Sources Identical)

```
raw.coingecko__coins_markets
────────────────────────────────────────────────────────────────────
id                  TEXT PRIMARY KEY       (uuid per record)
source              TEXT                   "coingecko"
entity              TEXT                   "coins_markets"
raw_data            JSONB                  original API response
is_valid            BOOLEAN                pydantic validation result
validation_errors   JSONB                  field-level error list
schema_version      TEXT                   "1.0"
loaded_at           TIMESTAMPTZ            ingestion timestamp
batch_id            TEXT                   groups records per flow run
```

### Adding a New Source — Checklist

```
1.  mkdir sources/{source_name}/
2.  create extractor.py        extend RestExtractor / GraphQLExtractor / CsvExtractor
3.  create loader.py           get_loader(config) via factory
4.  create schemas/{entity}.py Pydantic models per entity
5.  create __init__.py         self-register schemas + export extractor/loader
6.  create flows/sources/{source_name}_flow.py
7.  mkdir schedules/{source_name}/
8.  create events.py           event name constants
9.  create deployments.py      cron schedules + dbt deployments
10. create automations.py      event chains
11. add one line to schedules/orchestrator.py
```

Zero changes to `core/`, existing sources, or dbt models.

---

## 11. Open Discussion Points

These items need further design decisions before implementation.

---

### 11.1 Streaming / Real-time Sources

**Current state:** The `stream_extractor.py` base class is scaffolded but not fully designed.

**Questions to resolve:**
- What is the acceptable latency for WebSocket / Kafka sources? Seconds (true streaming) or minutes (micro-batch)?
- If true streaming is needed, should we introduce a dedicated stream processor (Faust, Bytewax) instead of running inside Prefect?
- How do streaming sources interact with the batch dbt transformation layer? Do they write to a separate `stream_raw` schema with its own transformation cadence?
- How do we handle schema evolution for high-volume streams where Pydantic validation overhead may matter?

---

### 11.2 Multi-target Fan-out

**Current state:** `settings.default_target` points to one warehouse. All sources write to that one target.

**Questions to resolve:**
- Do we need to write the same data to multiple warehouses simultaneously (e.g. Postgres for dev, BigQuery for prod)?
- If yes, the `DataWriter` needs a fan-out mode: `writer.write(batch)` sends to all configured targets, not just one.
- Should per-source target override be supported? (e.g. coingecko → Postgres, defillama → BigQuery)
- How do we handle partial failures in fan-out — if BigQuery write succeeds but Snowflake fails, do we retry only Snowflake?

---

### 11.3 Schema Versioning and Migration

**Current state:** `schema_version` field exists on `RawRecord` but version bumping is manual.

**Questions to resolve:**
- When a source API changes a field type (e.g. `price` goes from string to float), how do we bump `schema_version` and handle the transition in dbt staging models?
- Should we support reading multiple schema versions in staging (e.g. `WHERE schema_version IN ('1.0', '1.1')`) or enforce a hard cutover?
- Do we need an automated schema drift detector that compares incoming API responses against the registered Pydantic model and alerts before failures occur?

---

### 11.4 Backfill Strategy

**Current state:** No backfill mechanism is defined. Raw ingestion remains append-oriented; entity type determines downstream modeling strategy.

**Design decision:**
- Raw API responses are preserved as loaded and are not used as the primary deduplication boundary.
- Time-series facts such as prices, market caps, volumes, rankings, and TVL should be modeled as append-only or time-partitioned fact snapshots.
- Reference entities such as coins, exchanges, protocols, and metadata should be modeled as dimensions. Use SCD Type 2 where historical attribute changes matter; use Type 1 overwrite semantics where only the latest corrected state matters.
- Deterministic deduplication happens in dbt staging models on a per-model basis.
- Each staging model implements its deduplication logic directly in SQL using the model's natural key and ordering rules. Repeated dedup patterns can later be extracted into a shared dbt macro.

**Questions to resolve:**
- How do we trigger a historical backfill for a source? (e.g. re-ingest 90 days of CoinGecko market data)
- Should backfill be a separate Prefect flow deployment with date range parameters, or handled by re-running existing flows with override params?
- Do we need a separate `backfill_raw` schema to isolate backfill data from live data during processing?

---

### 11.5 Observability and Alerting

**Current state:** Prefect UI provides basic flow run visibility. Failure automation exists but only triggers a generic `notify-on-failure` deployment.

**Questions to resolve:**
- What alerting channels are required? Slack, PagerDuty, email?
- Should we track data quality metrics over time (e.g. `is_valid` rate per source per day) in a `monitoring` schema?
- Do we need SLA alerting — e.g. alert if `coingecko-get-assets` has not completed successfully by 01:00 UTC?
- Should dbt test failures produce a separate alert severity from EL failures?

---

### 11.6 Secret Management

**Current state:** API keys are pulled from env vars via `pydantic-settings`.

**Questions to resolve:**
- Is `.env` file sufficient for the target environment or do we need a secrets manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager)?
- Should API keys be stored as Prefect Blocks (native secret store) so they are managed in the Prefect UI and rotated without redeployment?
- How do we handle key rotation without restarting running flows mid-execution?

---

### 11.7 Testing Strategy

**Current state:** Test folders exist per source but no testing patterns are defined.

**Questions to resolve:**
- Unit tests: should we mock the HTTP client (`httpx` respx mocking) or use recorded fixtures (VCR cassettes)?
- Integration tests: do we spin up a local Postgres via `pytest-docker` or use a dedicated test database?
- dbt tests: are built-in `not_null` / `unique` tests sufficient or do we need custom data quality tests (e.g. price within expected range)?
- Should CI run dbt tests against a staging warehouse or a local DuckDB instance for speed?

---

### 11.8 CSV Import User Experience

**Current state:** `CsvImportExtractor` takes a `file_path` param but there is no defined import interface.

**Questions to resolve:**
- How do users provide CSVs? Via a web UI, S3 bucket drop, SFTP, or direct file path?
- Should CSV arrival trigger an immediate Prefect flow run (event-driven) or queue for the next scheduled batch?
- How do we validate CSV headers match the expected schema before ingestion starts?
- Where do we store uploaded files long-term — local disk, S3, GCS?

---

*End of Project Specifications v1.0.0*

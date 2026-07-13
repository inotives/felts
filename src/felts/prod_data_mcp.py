"""Felts production analytical data MCP server."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
import sqlglot
import yaml
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlglot import exp
from sqlglot.errors import ParseError

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_FILE = REPO_ROOT / "settings" / "felts-prod-data-views.txt"
DBT_MODELS_DIR = REPO_ROOT / "transforms" / "models"
MAX_ROWS = 1000
STATEMENT_TIMEOUT_MS = 15_000
IDLE_TRANSACTION_TIMEOUT_MS = 30_000
AUDIT_RETENTION_DAYS = 30

SAFE_FUNCTIONS = {
    "ABS",
    "AVG",
    "COALESCE",
    "COUNT",
    "DENSE_RANK",
    "EXTRACT",
    "LAG",
    "LEAD",
    "MAX",
    "MIN",
    "NULLIF",
    "RANK",
    "ROUND",
    "ROW_NUMBER",
    "SUM",
    # sqlglot normalizes PostgreSQL date_trunc to TimestampTrunc.
    "TIMESTAMP_TRUNC",
}


class PolicyError(ValueError):
    """Query violates the Felts production data policy."""


class ProdDataMcpSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    ssh_host: str = Field(alias="FELTS_MCP_SSH_HOST")
    ssh_user: str = Field(alias="FELTS_MCP_SSH_USER")
    ssh_port: int = Field(default=22, alias="FELTS_MCP_SSH_PORT")
    local_port: int = Field(default=15432, alias="FELTS_MCP_LOCAL_PORT")
    remote_host: str = Field(default="127.0.0.1", alias="FELTS_MCP_REMOTE_HOST")
    remote_port: int = Field(default=5432, alias="FELTS_MCP_REMOTE_PORT")
    db_name: str = Field(default="felts", alias="FELTS_MCP_DB_NAME")
    db_user: str = Field(default="felts_ai", alias="FELTS_MCP_DB_USER")
    db_password: str = Field(alias="FELTS_MCP_DB_PASSWORD")
    audit_log: Path = Field(
        default=Path("var/log/felts-prod-data/queries.jsonl"),
        alias="FELTS_MCP_AUDIT_LOG",
    )

    @property
    def conninfo(self) -> str:
        return (
            f"host=127.0.0.1 port={self.local_port} dbname={self.db_name} "
            f"user={self.db_user} password={self.db_password} "
            f"sslmode=disable options='-c statement_timeout={STATEMENT_TIMEOUT_MS} "
            f"-c idle_in_transaction_session_timeout={IDLE_TRANSACTION_TIMEOUT_MS}'"
        )

    @property
    def resolved_audit_log(self) -> Path:
        if self.audit_log.is_absolute():
            return self.audit_log
        return REPO_ROOT / self.audit_log


class ColumnMeta(BaseModel):
    name: str
    type: str


class QueryResult(BaseModel):
    columns: list[ColumnMeta]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool


def load_allowed_views(path: Path = ALLOWLIST_FILE) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    )


def load_dbt_descriptions(models_dir: Path = DBT_MODELS_DIR) -> dict[str, dict[str, Any]]:
    descriptions: dict[str, dict[str, Any]] = {}
    for path in models_dir.rglob("*.yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for model in data.get("models", []):
            name = model.get("name")
            if not name:
                continue
            descriptions[name] = {
                "description": model.get("description"),
                "columns": {
                    column["name"]: column.get("description")
                    for column in model.get("columns", [])
                    if column.get("name")
                },
            }
    return descriptions


def _qualified_table_name(table: exp.Table) -> str:
    if not table.db:
        return table.name
    return f"{table.db}.{table.name}"


def validate_query(sql: str, allowed_views: tuple[str, ...] | None = None) -> str:
    allowed = set(allowed_views or load_allowed_views())
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise PolicyError("SQL comments are not allowed")
    if ";" in sql:
        raise PolicyError("SQL semicolons are not allowed")

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except ParseError as exc:
        raise PolicyError(f"SQL parse failed: {exc}") from exc
    if len(statements) != 1:
        raise PolicyError("exactly one SQL statement is allowed")

    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise PolicyError("only SELECT statements are allowed")
    if any(tree.find_all(exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Command)):
        raise PolicyError("mutation and command statements are not allowed")

    cte_names = {cte.alias for cte in tree.find_all(exp.CTE) if cte.alias}
    for table in tree.find_all(exp.Table):
        if table.name in cte_names:
            continue
        table_name = _qualified_table_name(table)
        if table_name not in allowed:
            raise PolicyError(f"view is not allowlisted: {table_name}")

    for func in tree.find_all(exp.Func):
        if func.sql_name().upper() not in SAFE_FUNCTIONS:
            raise PolicyError(f"function is not allowlisted: {func.sql_name()}")

    if tree.args.get("limit") is None and not _is_unbounded_aggregate(tree):
        raise PolicyError("non-aggregate queries must include LIMIT")

    return tree.sql(dialect="postgres")


def _is_unbounded_aggregate(tree: exp.Select) -> bool:
    if tree.args.get("group") is not None:
        return False
    expressions = tree.expressions or []
    return bool(expressions) and all(expression.find(exp.AggFunc) for expression in expressions)


def describe_allowed_view(view_name: str, conninfo: str) -> dict[str, Any]:
    allowed = set(load_allowed_views())
    if view_name not in allowed:
        raise PolicyError(f"view is not allowlisted: {view_name}")
    schema, table = view_name.split(".", 1)

    with psycopg.connect(conninfo, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema, table),
            )
            columns = cur.fetchall()

    docs = load_dbt_descriptions().get(table, {})
    column_docs = docs.get("columns", {})
    return {
        "name": view_name,
        "description": docs.get("description"),
        "columns": [
            {
                "name": column["column_name"],
                "type": column["data_type"],
                "nullable": column["is_nullable"] == "YES",
                **(
                    {"description": column_docs[column["column_name"]]}
                    if column_docs.get(column["column_name"])
                    else {}
                ),
            }
            for column in columns
        ],
    }


def execute_query(sql: str, settings: ProdDataMcpSettings | None = None) -> QueryResult:
    active_settings = settings or ProdDataMcpSettings()
    started = time.monotonic()
    success = False
    row_count = 0
    error: str | None = None
    normalized_sql = ""
    try:
        normalized_sql = validate_query(sql)
        limited_sql = f"SELECT * FROM ({normalized_sql}) AS felts_mcp_query LIMIT {MAX_ROWS + 1}"
        with psycopg.connect(active_settings.conninfo, row_factory=dict_row) as conn:
            conn.read_only = True
            with conn.cursor() as cur:
                cur.execute(limited_sql)
                fetched = cur.fetchall()
                result = _query_result_from_rows(fetched, cur.description or [])
        row_count = result.row_count
        success = True
        return result
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        write_audit_log(
            active_settings.resolved_audit_log,
            sql_hash=_hash_sql(normalized_sql or sql),
            duration_ms=round((time.monotonic() - started) * 1000, 3),
            row_count=row_count,
            success=success,
            error=error,
        )


def _json_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _json_value(value) for key, value in row.items()}


def _query_result_from_rows(rows: list[dict[str, Any]], description: Any) -> QueryResult:
    returned_rows = rows[:MAX_ROWS]
    return QueryResult(
        columns=[
            ColumnMeta(name=column.name, type=_postgres_type_name(column.type_code))
            for column in description
        ],
        rows=[_json_row(row) for row in returned_rows],
        row_count=len(returned_rows),
        truncated=len(rows) > MAX_ROWS,
    )


def _postgres_type_name(type_code: int) -> str:
    type_info = psycopg.adapters.types.get(type_code)
    return type_info.name if type_info else str(type_code)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal | date | datetime):
        return str(value)
    return str(value)


def _hash_sql(sql: str) -> str:
    normalized = " ".join(sql.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def write_audit_log(
    path: Path,
    *,
    sql_hash: str,
    duration_ms: float,
    row_count: int,
    success: bool,
    error: str | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "sql_sha256": sql_hash,
        "duration_ms": duration_ms,
        "row_count": row_count,
        "success": success,
    }
    if error:
        event["error"] = error
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, sort_keys=True) + "\n")


def prune_audit_log(path: Path, *, now: datetime | None = None) -> None:
    if not path.exists():
        return
    cutoff = (now or datetime.now(UTC)) - timedelta(days=AUDIT_RETENTION_DAYS)
    kept: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
            timestamp = datetime.fromisoformat(event["timestamp"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if timestamp >= cutoff:
            kept.append(line)
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def create_server() -> Any:
    from mcp.server.fastmcp import FastMCP

    settings = ProdDataMcpSettings()
    mcp = FastMCP("felts-prod-data")

    @mcp.tool()
    def list_views() -> list[str]:
        """List allowlisted Felts production analytical views."""
        return list(load_allowed_views())

    @mcp.tool()
    def describe_view(view_name: str) -> dict[str, Any]:
        """Describe one allowlisted view."""
        return describe_allowed_view(view_name, settings.conninfo)

    @mcp.tool()
    def query(sql: str) -> dict[str, Any]:
        """Run one bounded analytical SELECT query."""
        return execute_query(sql, settings).model_dump()

    return mcp


def check_database(settings: ProdDataMcpSettings | None = None) -> None:
    active_settings = settings or ProdDataMcpSettings()
    with psycopg.connect(active_settings.conninfo) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()


def main() -> None:
    if sys.argv[1:] == ["--check-db"]:
        check_database()
        return
    if sys.argv[1:] == ["--prune-audit-log"]:
        settings = ProdDataMcpSettings()
        prune_audit_log(settings.resolved_audit_log)
        return
    create_server().run()


if __name__ == "__main__":
    main()

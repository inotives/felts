import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from felts.prod_data_mcp import (
    MAX_ROWS,
    PolicyError,
    _json_value,
    _query_result_from_rows,
    describe_allowed_view,
    load_allowed_views,
    load_dbt_descriptions,
    prune_audit_log,
    validate_query,
    write_audit_log,
)


def test_load_allowed_views_reads_committed_allowlist() -> None:
    assert load_allowed_views() == (
        "coingecko.mart_coingecko__asset_platforms",
        "coingecko.mart_coingecko__coins",
        "public.stg_alphavantage__time_series_daily",
        "coingecko.stg_coingecko__asset_platforms_list",
        "coingecko.stg_coingecko__coins_list",
        "coingecko.stg_coingecko__coins_markets",
        "coingecko.stg_coingecko__global",
        "coingecko.stg_coingecko__global_defi",
        "csv_import.stg_csv_import__fred_series",
        "csv_import.stg_csv_import__ohlcv",
    )


def test_validate_query_allows_bounded_select_from_allowlisted_view() -> None:
    sql = "select coin_id from coingecko.mart_coingecko__coins limit 10"

    assert validate_query(sql) == "SELECT coin_id FROM coingecko.mart_coingecko__coins LIMIT 10"


def test_validate_query_allows_unbounded_aggregate() -> None:
    sql = "select count(*) from public.stg_alphavantage__time_series_daily"

    assert validate_query(sql) == "SELECT COUNT(*) FROM public.stg_alphavantage__time_series_daily"


@pytest.mark.parametrize(
    "sql",
    [
        "select * from raw.raw_coins limit 10",
        "delete from mart_coingecko__coins",
        "select * from mart_coingecko__coins limit 10",
        "select coin_id from mart_coingecko__coins",
        "select now() from coingecko.mart_coingecko__coins limit 1",
        "select coin_id from coingecko.mart_coingecko__coins; select 1",
        "select coin_id from coingecko.mart_coingecko__coins -- no",
    ],
)
def test_validate_query_rejects_unsafe_sql(sql: str) -> None:
    with pytest.raises(PolicyError):
        validate_query(sql)


def test_describe_allowed_view_uses_schema_qualified_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[str, str]]] = []

    class Cursor:
        def __enter__(self) -> "Cursor":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, sql: str, params: tuple[str, str]) -> None:
            calls.append((sql, params))

        def fetchall(self) -> list[dict[str, str]]:
            return [
                {
                    "column_name": "coin_id",
                    "data_type": "text",
                    "is_nullable": "NO",
                }
            ]

    class Connection:
        def __enter__(self) -> "Connection":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def cursor(self) -> Cursor:
            return Cursor()

    monkeypatch.setattr(
        "felts.prod_data_mcp.psycopg.connect",
        lambda *args, **kwargs: Connection(),
    )

    description = describe_allowed_view("coingecko.mart_coingecko__coins", "dbname=x")

    assert calls == [
        (
            """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
            ("coingecko", "mart_coingecko__coins"),
        )
    ]
    assert description["name"] == "coingecko.mart_coingecko__coins"
    assert description["columns"][0]["name"] == "coin_id"


def test_json_value_preserves_json_scalars_and_stringifies_decimal() -> None:
    assert _json_value(None) is None
    assert _json_value(True) is True
    assert _json_value(1) == 1
    assert _json_value(Decimal("1.23")) == "1.23"


def test_query_result_serializes_and_marks_truncated() -> None:
    result = _query_result_from_rows(
        [{"value": Decimal("1.23")} for _ in range(MAX_ROWS + 1)],
        [SimpleNamespace(name="value", type_code=1700)],
    )

    assert result.columns[0].name == "value"
    assert result.columns[0].type == "numeric"
    assert result.rows[0]["value"] == "1.23"
    assert result.row_count == MAX_ROWS
    assert result.truncated is True


def test_load_dbt_descriptions_includes_model_descriptions() -> None:
    descriptions = load_dbt_descriptions()

    assert (
        descriptions["stg_alphavantage__time_series_daily"]["description"]
        == "Alpha Vantage daily prices at one row per symbol and trading date."
    )


def test_write_audit_log_omits_sql_text_and_results(tmp_path: Path) -> None:
    path = tmp_path / "queries.jsonl"

    write_audit_log(
        path,
        sql_hash="abc123",
        duration_ms=1.5,
        row_count=2,
        success=True,
        error=None,
    )

    event = json.loads(path.read_text())
    assert event["sql_sha256"] == "abc123"
    assert event["row_count"] == 2
    assert "sql" not in event
    assert "rows" not in event


def test_prune_audit_log_removes_entries_older_than_retention(tmp_path: Path) -> None:
    path = tmp_path / "queries.jsonl"
    now = datetime(2026, 6, 26, tzinfo=UTC)
    old = {"timestamp": (now - timedelta(days=31)).isoformat(), "sql_sha256": "old"}
    kept = {"timestamp": (now - timedelta(days=1)).isoformat(), "sql_sha256": "kept"}
    path.write_text(json.dumps(old) + "\n" + json.dumps(kept) + "\n", encoding="utf-8")

    prune_audit_log(path, now=now)

    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert events == [kept]

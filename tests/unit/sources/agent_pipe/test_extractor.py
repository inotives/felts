import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from felts.core.exceptions import ExtractionError
from felts.sources.agent_pipe import AgentPipeSQLiteExtractor


def test_extracts_records_from_agent_pipe_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "local.sqlite"
    _create_records_db(db_path)
    _insert_record(
        db_path,
        id="rec_1",
        project_id="agent-pipe",
        entity="note",
        local_id="local-1",
        source="manual",
        captured_at="2026-07-14T01:02:03.000Z",
        payload_json={"title": "First"},
        metadata_json={"run_id": "run_1"},
        deleted_at=None,
    )
    _insert_record(
        db_path,
        id="rec_2",
        project_id="agent-pipe",
        entity="note",
        local_id="local-2",
        source=None,
        captured_at=None,
        payload_json={"title": "Deleted"},
        metadata_json=None,
        deleted_at="2026-07-14T02:00:00.000Z",
    )

    records = list(AgentPipeSQLiteExtractor(sqlite_path=db_path).extract())

    assert [record.source_record_id for record in records] == ["rec_1", "rec_2"]
    assert records[0].source == "agent_pipe"
    assert records[0].entity == "note"
    assert records[0].payload == {
        "agent_pipe": {
            "id": "rec_1",
            "project_id": "agent-pipe",
            "local_id": "local-1",
            "source": "manual",
            "captured_at": "2026-07-14T01:02:03.000Z",
            "metadata": {"run_id": "run_1"},
            "created_at": "2026-07-14T01:02:04.000Z",
            "updated_at": "2026-07-14T01:02:05.000Z",
            "deleted_at": None,
        },
        "payload": {"title": "First"},
    }
    assert records[1].payload["agent_pipe"]["deleted_at"] == "2026-07-14T02:00:00.000Z"
    assert records[1].payload["agent_pipe"]["metadata"] == {}


def test_malformed_payload_json_fails_clearly(tmp_path: Path) -> None:
    db_path = tmp_path / "local.sqlite"
    _create_records_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO records (
                id, project_id, entity, local_id, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "rec_bad",
                "agent-pipe",
                "note",
                "local-bad",
                "{not json",
                "2026-07-14T01:02:04.000Z",
                "2026-07-14T01:02:05.000Z",
            ),
        )

    with pytest.raises(ExtractionError, match="rec_bad.*payload_json"):
        list(AgentPipeSQLiteExtractor(sqlite_path=db_path).extract())


def test_updated_since_filters_rows_and_keeps_matching_soft_deletes(tmp_path: Path) -> None:
    db_path = tmp_path / "local.sqlite"
    _create_records_db(db_path)
    _insert_record(
        db_path,
        id="rec_old",
        project_id="agent-pipe",
        entity="note",
        local_id="local-old",
        source=None,
        captured_at=None,
        payload_json={"title": "Old"},
        metadata_json=None,
        updated_at="2026-07-14T01:00:00Z",
        deleted_at=None,
    )
    _insert_record(
        db_path,
        id="rec_deleted",
        project_id="agent-pipe",
        entity="note",
        local_id="local-deleted",
        source=None,
        captured_at=None,
        payload_json={"title": "Deleted"},
        metadata_json=None,
        updated_at="2026-07-14T03:00:00Z",
        deleted_at="2026-07-14T03:00:00Z",
    )

    filtered = list(
        AgentPipeSQLiteExtractor(
            sqlite_path=db_path,
            updated_since="2026-07-14T02:00:00Z",
        ).extract()
    )
    unfiltered = list(AgentPipeSQLiteExtractor(sqlite_path=db_path).extract())

    assert [record.source_record_id for record in filtered] == ["rec_deleted"]
    assert filtered[0].payload["agent_pipe"]["deleted_at"] == "2026-07-14T03:00:00Z"
    assert [record.source_record_id for record in unfiltered] == [
        "rec_deleted",
        "rec_old",
    ]


def test_malformed_metadata_json_fails_clearly(tmp_path: Path) -> None:
    db_path = tmp_path / "local.sqlite"
    _create_records_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO records (
                id, project_id, entity, local_id, payload_json, metadata_json,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "rec_bad_meta",
                "agent-pipe",
                "note",
                "local-bad-meta",
                "{}",
                "{not json",
                "2026-07-14T01:02:04.000Z",
                "2026-07-14T01:02:05.000Z",
            ),
        )

    with pytest.raises(ExtractionError, match="rec_bad_meta.*metadata_json"):
        list(AgentPipeSQLiteExtractor(sqlite_path=db_path).extract())


def _create_records_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE records (
                id text primary key,
                project_id text not null,
                entity text not null,
                local_id text not null,
                source text,
                captured_at text,
                payload_json text not null,
                metadata_json text,
                created_at text not null,
                updated_at text not null,
                deleted_at text
            )
            """
        )


def _insert_record(
    db_path: Path,
    *,
    id: str,
    project_id: str,
    entity: str,
    local_id: str,
    source: str | None,
    captured_at: str | None,
    payload_json: dict[str, Any],
    metadata_json: dict[str, Any] | None,
    updated_at: str = "2026-07-14T01:02:05.000Z",
    deleted_at: str | None = None,
) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO records (
                id,
                project_id,
                entity,
                local_id,
                source,
                captured_at,
                payload_json,
                metadata_json,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id,
                project_id,
                entity,
                local_id,
                source,
                captured_at,
                json.dumps(payload_json),
                json.dumps(metadata_json) if metadata_json is not None else None,
                "2026-07-14T01:02:04.000Z",
                updated_at,
                deleted_at,
            ),
        )

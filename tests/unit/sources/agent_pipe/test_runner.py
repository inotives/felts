import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from felts.core.loaders import LoadResult, RawWriter
from felts.core.schemas import RawRecord, SchemaRegistry
from felts.sources.agent_pipe.runner import run_agent_pipe_import


class MemoryLoader:
    def __init__(self) -> None:
        self.records: list[RawRecord] = []

    def write_records(self, records: Sequence[RawRecord]) -> LoadResult:
        self.records.extend(records)
        return LoadResult(inserted_count=len(records))


def test_run_agent_pipe_import_writes_entity_summaries(tmp_path: Path) -> None:
    db_path = tmp_path / "local.sqlite"
    _create_records_db(db_path)
    _insert_record(
        db_path,
        id="rec_1",
        entity="note",
        payload={"title": "one"},
        updated_at="2026-07-14T01:00:00Z",
    )
    _insert_record(
        db_path,
        id="rec_2",
        entity="task",
        payload={"title": "two"},
        updated_at="2026-07-14T03:00:00Z",
    )

    loader = MemoryLoader()
    writer = RawWriter(schema_registry=SchemaRegistry(), loader=loader)

    summary = run_agent_pipe_import(sqlite_path=db_path, writer=writer)

    assert summary.source == "agent_pipe"
    assert [(item.entity, item.extracted_count) for item in summary.entities] == [
        ("note", 1),
        ("task", 1),
    ]
    assert [(record.source, record.entity) for record in loader.records] == [
        ("agent_pipe", "note"),
        ("agent_pipe", "task"),
    ]


def test_run_agent_pipe_import_passes_updated_since(tmp_path: Path) -> None:
    db_path = tmp_path / "local.sqlite"
    _create_records_db(db_path)
    _insert_record(
        db_path,
        id="rec_old",
        entity="note",
        payload={"title": "old"},
        updated_at="2026-07-14T01:00:00Z",
    )
    _insert_record(
        db_path,
        id="rec_new",
        entity="note",
        payload={"title": "new"},
        updated_at="2026-07-14T03:00:00Z",
    )
    loader = MemoryLoader()
    writer = RawWriter(schema_registry=SchemaRegistry(), loader=loader)

    summary = run_agent_pipe_import(
        sqlite_path=db_path,
        updated_since="2026-07-14T02:00:00Z",
        writer=writer,
    )

    assert summary.entities[0].extracted_count == 1
    assert loader.records[0].source_record_id == "rec_new"


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
    entity: str,
    payload: object,
    updated_at: str,
) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO records (
                id, project_id, entity, local_id, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id,
                "agent-pipe",
                entity,
                id,
                json.dumps(payload),
                "2026-07-14T01:02:04.000Z",
                updated_at,
            ),
        )

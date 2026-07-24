"""agent-pipe SQLite extractor."""

import json
import re
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from felts.core.exceptions import ExtractionError
from felts.core.schemas import ExtractedRecord


class AgentPipeSQLiteExtractor:
    """Extract agent-pipe records rows into Felts records."""

    def __init__(
        self,
        *,
        sqlite_path: str | Path,
        updated_since: str | datetime | None = None,
    ) -> None:
        self.sqlite_path = Path(sqlite_path)
        self.updated_since = _parse_iso_datetime(updated_since, field_name="updated_since")

    def extract(self) -> Iterable[ExtractedRecord]:
        with sqlite3.connect(self.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT
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
                FROM records
                ORDER BY id
                """
            )
            for row in rows:
                if self.updated_since is not None and _row_updated_at(row) <= self.updated_since:
                    continue
                yield _record(row)


def _record(row: sqlite3.Row) -> ExtractedRecord:
    row_id = str(row["id"])
    metadata = _parse_json(row["metadata_json"], field_name="metadata_json", row_id=row_id)
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        msg = f"agent-pipe record {row_id} metadata_json must be a JSON object"
        raise ExtractionError(msg)

    return ExtractedRecord(
        source=_source_identifier(str(row["project_id"])),
        entity=str(row["entity"]),
        source_record_id=row_id,
        payload={
            "agent_pipe": {
                "id": row_id,
                "project_id": row["project_id"],
                "local_id": row["local_id"],
                "source": row["source"],
                "captured_at": row["captured_at"],
                "metadata": metadata,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "deleted_at": row["deleted_at"],
            },
            "payload": _parse_json(row["payload_json"], field_name="payload_json", row_id=row_id),
        },
    )


def _parse_json(value: str | None, *, field_name: str, row_id: str) -> Any:
    if value in (None, "") and field_name == "metadata_json":
        return None
    try:
        return json.loads(value or "")
    except json.JSONDecodeError as exc:
        msg = f"agent-pipe record {row_id} has malformed {field_name}"
        raise ExtractionError(msg) from exc


def _source_identifier(project_id: str) -> str:
    source = re.sub(r"[^a-z0-9]+", "_", project_id.lower()).strip("_")
    if not source:
        msg = "agent-pipe project_id must contain at least one alphanumeric character"
        raise ExtractionError(msg)
    return source


def _row_updated_at(row: sqlite3.Row) -> datetime:
    value = row["updated_at"]
    if not isinstance(value, str):
        msg = f"agent-pipe record {row['id']} updated_at must be an ISO timestamp"
        raise ExtractionError(msg)
    parsed = _parse_iso_datetime(value, field_name="updated_at")
    if parsed is None:
        msg = f"agent-pipe record {row['id']} updated_at must be an ISO timestamp"
        raise ExtractionError(msg)
    return parsed


def _parse_iso_datetime(value: str | datetime | None, *, field_name: str) -> datetime | None:
    if value is None or isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO timestamp"
            raise ExtractionError(msg) from exc
    if parsed is not None and (parsed.tzinfo is None or parsed.utcoffset() is None):
        return parsed.replace(tzinfo=UTC)
    return parsed

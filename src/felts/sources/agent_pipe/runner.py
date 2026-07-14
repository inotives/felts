"""Plain Python agent-pipe SQLite import runner."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from felts.config import Settings, get_settings
from felts.core.loaders import RawWriter, create_loader
from felts.core.schemas import ExtractedRecord, SchemaRegistry
from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.agent_pipe.extractor import AgentPipeSQLiteExtractor


def run_agent_pipe_import(
    *,
    sqlite_path: str | Path,
    updated_since: str | None = None,
    settings: Settings | None = None,
    writer: RawWriter | None = None,
) -> SourceRunSummary:
    started_at = datetime.now(UTC)
    settings = settings or get_settings()
    if writer is None:
        writer = RawWriter(
            schema_registry=SchemaRegistry(),
            loader=create_loader(settings),
            loader_batch_size=settings.loader_batch_size,
        )

    by_entity = _group_by_entity(
        AgentPipeSQLiteExtractor(
            sqlite_path=sqlite_path,
            updated_since=updated_since,
        ).extract()
    )
    entity_summaries = [
        EntityRunSummary.from_write_result(entity=entity, result=writer.write(records))
        for entity, records in by_entity.items()
    ]

    return SourceRunSummary(
        source=next(iter(by_entity.values()))[0].source if by_entity else "agent_pipe",
        started_at=started_at,
        ended_at=datetime.now(UTC),
        entities=tuple(entity_summaries),
    )


def _group_by_entity(
    records: Iterable[ExtractedRecord],
) -> dict[str, list[ExtractedRecord]]:
    grouped: dict[str, list[ExtractedRecord]] = defaultdict(list)
    for record in records:
        grouped[record.entity].append(record)
    return grouped

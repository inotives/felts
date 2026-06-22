from datetime import UTC, datetime
from typing import Any

from pytest import MonkeyPatch

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.csv_import.events import (
    emit_raw_completion_events,
    raw_completion_event_name,
    raw_completion_payload,
    should_emit_raw_completion_event,
)


def test_raw_completion_event_payload_includes_transform_selector() -> None:
    summary = _entity_summary(entity="fred_series", inserted_count=2)

    assert raw_completion_event_name("fred_series") == "felts.raw.csv_import.fred_series.completed"
    assert raw_completion_payload(summary)["dbt_selector"] == "stg_csv_import__fred_series+"


def test_raw_completion_event_gate_requires_valid_inserted_rows() -> None:
    assert should_emit_raw_completion_event(_entity_summary(inserted_count=1)) is True
    invalid = _entity_summary(inserted_count=1, invalid_count=1)
    failed = _entity_summary(inserted_count=1, failed_count=1)
    assert should_emit_raw_completion_event(invalid) is False
    assert should_emit_raw_completion_event(failed) is False


def test_emit_raw_completion_events_emits_inserted_entities(monkeypatch: MonkeyPatch) -> None:
    emitted: list[dict[str, Any]] = []

    def fake_emit_event(**kwargs: Any) -> None:
        emitted.append(kwargs)

    monkeypatch.setattr("felts.sources.csv_import.events.emit_event", fake_emit_event)
    summary = SourceRunSummary(
        source="csv_import",
        started_at=datetime.now(UTC),
        entities=(_entity_summary(entity="ohlcv", inserted_count=1),),
    )

    emitted_events = emit_raw_completion_events(summary)

    assert emitted_events == ["felts.raw.csv_import.ohlcv.completed"]
    assert emitted[0]["resource"]["prefect.resource.id"] == "felts.raw.csv_import.ohlcv"


def _entity_summary(
    *,
    entity: str = "ohlcv",
    inserted_count: int,
    invalid_count: int = 0,
    failed_count: int = 0,
) -> EntityRunSummary:
    return EntityRunSummary(
        entity=entity,
        batch_id="batch-1",
        extracted_count=3,
        inserted_count=inserted_count,
        skipped_duplicate_count=0,
        invalid_count=invalid_count,
        failed_count=failed_count,
    )

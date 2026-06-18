from datetime import UTC, datetime
from typing import Any

from pytest import MonkeyPatch

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.coingecko.events import (
    emit_raw_completion_events,
    raw_completion_event_name,
    raw_completion_payload,
    should_emit_raw_completion_event,
)


def test_raw_completion_event_payload_includes_transform_selector() -> None:
    summary = _entity_summary(entity="coins_list", inserted_count=2)

    assert raw_completion_event_name("coins_list") == "felts.raw.coingecko.coins_list.completed"
    assert raw_completion_payload(summary) == {
        "source": "coingecko",
        "entity": "coins_list",
        "batch_id": "batch-1",
        "inserted_count": 2,
        "skipped_count": 0,
        "extracted_count": 3,
        "failed_count": 0,
        "dbt_selector": "stg_coingecko__coins_list+",
    }


def test_raw_completion_event_gate_requires_inserted_rows() -> None:
    assert should_emit_raw_completion_event(_entity_summary(inserted_count=1)) is True
    assert should_emit_raw_completion_event(_entity_summary(inserted_count=0)) is False
    failed_summary = _entity_summary(inserted_count=1, failed_count=1)
    assert should_emit_raw_completion_event(failed_summary) is False


def test_emit_raw_completion_events_emits_inserted_entities(monkeypatch: MonkeyPatch) -> None:
    emitted: list[dict[str, Any]] = []

    def fake_emit_event(**kwargs: Any) -> None:
        emitted.append(kwargs)

    monkeypatch.setattr("felts.sources.coingecko.events.emit_event", fake_emit_event)
    summary = SourceRunSummary(
        source="coingecko",
        started_at=datetime.now(UTC),
        entities=(
            _entity_summary(entity="coins_list", inserted_count=1),
            _entity_summary(entity="global", inserted_count=0),
        ),
    )

    emitted_events = emit_raw_completion_events(summary)

    assert emitted_events == ["felts.raw.coingecko.coins_list.completed"]
    assert emitted[0]["resource"]["prefect.resource.id"] == "felts.raw.coingecko.coins_list"
    assert emitted[0]["payload"]["dbt_selector"] == "stg_coingecko__coins_list+"


def _entity_summary(
    *, entity: str = "coins_list", inserted_count: int, failed_count: int = 0
) -> EntityRunSummary:
    return EntityRunSummary(
        entity=entity,
        batch_id="batch-1",
        extracted_count=3,
        inserted_count=inserted_count,
        skipped_duplicate_count=0,
        invalid_count=0,
        failed_count=failed_count,
    )

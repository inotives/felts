"""CSV import Prefect event helpers."""

from typing import Any

from prefect.events import emit_event

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.csv_import.contracts import CSV_IMPORT_SOURCE, get_csv_contract


def raw_completion_event_name(entity: str) -> str:
    return f"felts.raw.{CSV_IMPORT_SOURCE}.{entity}.completed"


def raw_completion_resource_id(entity: str) -> str:
    return f"felts.raw.{CSV_IMPORT_SOURCE}.{entity}"


def raw_completion_payload(entity_summary: EntityRunSummary) -> dict[str, Any]:
    contract = get_csv_contract(entity_summary.entity)
    return {
        "source": CSV_IMPORT_SOURCE,
        "entity": entity_summary.entity,
        "batch_id": entity_summary.batch_id,
        "inserted_count": entity_summary.inserted_count,
        "skipped_count": entity_summary.skipped_duplicate_count,
        "extracted_count": entity_summary.extracted_count,
        "failed_count": entity_summary.failed_count,
        "dbt_selector": contract.dbt_selector,
    }


def should_emit_raw_completion_event(entity_summary: EntityRunSummary) -> bool:
    valid_inserted_count = entity_summary.inserted_count - entity_summary.invalid_count
    return valid_inserted_count > 0 and entity_summary.failed_count == 0


def emit_raw_completion_events(summary: SourceRunSummary) -> list[str]:
    emitted_events: list[str] = []
    for entity_summary in summary.entities:
        if not should_emit_raw_completion_event(entity_summary):
            continue
        event_name = raw_completion_event_name(entity_summary.entity)
        emit_event(
            event=event_name,
            resource={
                "prefect.resource.id": raw_completion_resource_id(entity_summary.entity),
                "felts.source": CSV_IMPORT_SOURCE,
                "felts.entity": entity_summary.entity,
            },
            payload=raw_completion_payload(entity_summary),
        )
        emitted_events.append(event_name)
    return emitted_events

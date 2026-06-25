"""Generated Alphavantage Prefect event helpers."""

from typing import Any

from prefect.events import emit_event

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.alphavantage.constants import ALPHAVANTAGE_SOURCE, DBT_SELECTORS


def raw_completion_event_name(entity: str) -> str:
    return f"felts.raw.{ALPHAVANTAGE_SOURCE}.{entity}.completed"


def raw_completion_resource_id(entity: str) -> str:
    return f"felts.raw.{ALPHAVANTAGE_SOURCE}.{entity}"


def raw_completion_payload(summary: EntityRunSummary) -> dict[str, Any]:
    return {
        "source": ALPHAVANTAGE_SOURCE,
        "entity": summary.entity,
        "batch_id": summary.batch_id,
        "inserted_count": summary.inserted_count,
        "skipped_count": summary.skipped_duplicate_count,
        "extracted_count": summary.extracted_count,
        "failed_count": summary.failed_count,
        "dbt_selector": DBT_SELECTORS[summary.entity],
    }


def emit_raw_completion_events(summary: SourceRunSummary) -> list[str]:
    emitted = []
    for entity in summary.entities:
        if entity.inserted_count <= 0 or entity.failed_count:
            continue
        event_name = raw_completion_event_name(entity.entity)
        emit_event(
            event=event_name,
            resource={
                "prefect.resource.id": raw_completion_resource_id(entity.entity),
                "felts.source": ALPHAVANTAGE_SOURCE,
                "felts.entity": entity.entity,
            },
            payload=raw_completion_payload(entity),
        )
        emitted.append(event_name)
    return emitted

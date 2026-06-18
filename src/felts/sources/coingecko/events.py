"""CoinGecko Prefect event helpers."""

from typing import Any, cast

from prefect.events import emit_event

from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.coingecko.constants import COINGECKO_SOURCE, DBT_SELECTORS, CoinGeckoEntity


def raw_completion_event_name(entity: str) -> str:
    return f"felts.raw.{COINGECKO_SOURCE}.{entity}.completed"


def raw_completion_resource_id(entity: str) -> str:
    return f"felts.raw.{COINGECKO_SOURCE}.{entity}"


def raw_completion_payload(entity_summary: EntityRunSummary) -> dict[str, Any]:
    entity = coingecko_entity_from_string(entity_summary.entity)
    return {
        "source": COINGECKO_SOURCE,
        "entity": entity_summary.entity,
        "batch_id": entity_summary.batch_id,
        "inserted_count": entity_summary.inserted_count,
        "skipped_count": entity_summary.skipped_duplicate_count,
        "extracted_count": entity_summary.extracted_count,
        "failed_count": entity_summary.failed_count,
        "dbt_selector": DBT_SELECTORS[entity],
    }


def should_emit_raw_completion_event(entity_summary: EntityRunSummary) -> bool:
    return entity_summary.inserted_count > 0 and entity_summary.failed_count == 0


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
                "felts.source": COINGECKO_SOURCE,
                "felts.entity": entity_summary.entity,
            },
            payload=raw_completion_payload(entity_summary),
        )
        emitted_events.append(event_name)
    return emitted_events


def coingecko_entity_from_string(entity: str) -> CoinGeckoEntity:
    if entity not in DBT_SELECTORS:
        msg = f"unsupported CoinGecko entity for event mapping: {entity}"
        raise ValueError(msg)
    return cast(CoinGeckoEntity, entity)

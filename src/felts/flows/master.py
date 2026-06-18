"""Manual run-anytime orchestration flow."""

from collections.abc import Sequence

from prefect import flow

from felts.flows.transform import transform_flow
from felts.sources.coingecko.constants import DBT_SELECTORS, SUPPORTED_ENTITIES
from felts.sources.coingecko.events import coingecko_entity_from_string
from felts.sources.coingecko.flow import coingecko_entity_source_flow


@flow(name="felts-master")
def master_flow(source: str = "coingecko", entities: Sequence[str] | None = None) -> None:
    if source != "coingecko":
        msg = f"unsupported source for master flow: {source}"
        raise ValueError(msg)

    selected_entities = tuple(entities) if entities is not None else SUPPORTED_ENTITIES
    for entity in selected_entities:
        coingecko_entity = coingecko_entity_from_string(entity)
        summary = coingecko_entity_source_flow(entity)
        entity_summary = summary.entities[0]
        if entity_summary.inserted_count > 0 and entity_summary.failed_count == 0:
            transform_flow(selector=DBT_SELECTORS[coingecko_entity])

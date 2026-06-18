"""CoinGecko Prefect source flows."""

from collections.abc import Sequence

from prefect import flow

from felts.core.sources import SourceRunSummary
from felts.sources.coingecko.events import emit_raw_completion_events
from felts.sources.coingecko.runner import run_coingecko_source


@flow(name="coingecko-entity-source", retries=2, retry_delay_seconds=60)
def coingecko_entity_source_flow(entity: str) -> SourceRunSummary:
    summary = run_coingecko_source(entities=[entity])
    emit_raw_completion_events(summary)
    return summary


@flow(name="coingecko-source", retries=2, retry_delay_seconds=60)
def coingecko_source_flow(entities: Sequence[str] | None = None) -> SourceRunSummary:
    summary = run_coingecko_source(entities=entities)
    emit_raw_completion_events(summary)
    return summary

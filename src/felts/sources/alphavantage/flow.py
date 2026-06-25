"""Generated Alphavantage Prefect source flow."""

from collections.abc import Mapping, Sequence

from prefect import flow

from felts.core.sources import SourceRunSummary
from felts.sources.alphavantage.events import emit_raw_completion_events
from felts.sources.alphavantage.runner import run_alphavantage_source


@flow(name="alphavantage-source", retries=2, retry_delay_seconds=60)
def alphavantage_source_flow(
    entities: Sequence[str],
    runtime_params: Mapping[str, Sequence[str]],
) -> SourceRunSummary:
    summary = run_alphavantage_source(
        entities=entities,
        runtime_params=runtime_params,
    )
    emit_raw_completion_events(summary)
    return summary

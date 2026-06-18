"""Thin Prefect-compatible wrapper for the CoinGecko source."""

from collections.abc import Sequence

from prefect import flow

from felts.core.sources import SourceRunSummary
from felts.sources.coingecko.runner import run_coingecko_source


@flow(name="coingecko-source")
def coingecko_source_flow(entities: Sequence[str] | None = None) -> SourceRunSummary:
    return run_coingecko_source(entities=entities)

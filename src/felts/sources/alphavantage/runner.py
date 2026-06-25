"""Generated Alphavantage source runner."""

# ruff: noqa: I001

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from pydantic import BaseModel

from felts.config import Settings, get_settings
from felts.core.exceptions import ConfigurationError
from felts.core.extractors.rest import RestClient
from felts.core.loaders import RawWriter, create_loader
from felts.core.schemas import SchemaRegistry
from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.alphavantage.constants import (
    ALPHAVANTAGE_BASE_URL,
    ALPHAVANTAGE_SOURCE,
    SUPPORTED_ENTITIES,
)
from felts.sources.alphavantage.extractor import AlphavantageExtractor

# scaffold: schema-imports:start
from felts.sources.alphavantage.schemas import TimeSeriesDailyPayload
# scaffold: schema-imports:end

SCHEMA_VERSION = "1"


def build_alphavantage_schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    registrations: dict[str, type[BaseModel]] = {
        # scaffold: schema-registrations:start
        "time_series_daily": TimeSeriesDailyPayload,
        # scaffold: schema-registrations:end
    }
    for entity, model in registrations.items():
        registry.register(
            source=ALPHAVANTAGE_SOURCE,
            entity=entity,
            model=model,
            schema_name=f"alphavantage_{entity}",
            schema_version=SCHEMA_VERSION,
        )
    return registry


def run_alphavantage_source(
    *,
    entities: Sequence[str] | None = None,
    runtime_params: Mapping[str, Sequence[str]] | None = None,
    settings: Settings | None = None,
    extractor: AlphavantageExtractor | None = None,
    writer: RawWriter | None = None,
) -> SourceRunSummary:
    started_at = datetime.now(UTC)
    settings = settings or get_settings()
    selected = tuple(entities) if entities is not None else SUPPORTED_ENTITIES
    unsupported = set(selected) - set(SUPPORTED_ENTITIES)
    if unsupported:
        raise ValueError(f"unsupported Alphavantage entities: {sorted(unsupported)}")

    owns_client = extractor is None
    client = None
    if extractor is None:
        if not settings.alphavantage_api_key:
            raise ConfigurationError("ALPHAVANTAGE_API_KEY is required")
        client = _build_rest_client(settings)
        extractor = AlphavantageExtractor(
            client=client,
            api_key=settings.alphavantage_api_key,
        )
    if writer is None:
        writer = RawWriter(
            schema_registry=build_alphavantage_schema_registry(),
            loader=create_loader(settings),
            loader_batch_size=settings.loader_batch_size,
        )

    summaries = []
    try:
        for entity in selected:
            records = extractor.extract_entity(entity, runtime_params=runtime_params)
            result = writer.write(records)
            summaries.append(EntityRunSummary.from_write_result(entity=entity, result=result))
    finally:
        if owns_client and client is not None:
            client.close()
    return SourceRunSummary(
        source=ALPHAVANTAGE_SOURCE,
        started_at=started_at,
        ended_at=datetime.now(UTC),
        entities=tuple(summaries),
    )


def _build_rest_client(_settings: Settings) -> RestClient:
    return RestClient(base_url=ALPHAVANTAGE_BASE_URL)

"""Plain Python CoinGecko source runner."""

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from typing import cast

from pydantic import BaseModel

from felts.config import Settings, get_settings
from felts.core.exceptions import ConfigurationError
from felts.core.extractors.rest import RestClient
from felts.core.loaders import RawWriter, create_loader
from felts.core.schemas import SchemaRegistry
from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.coingecko.constants import (
    COINGECKO_SOURCE,
    SUPPORTED_ENTITIES,
    CoinGeckoEntity,
)
from felts.sources.coingecko.extractor import CoinGeckoExtractor
from felts.sources.coingecko.schemas import (
    AssetPlatformsListPayload,
    CoinsListPayload,
    CoinsMarketsPayload,
    GlobalDefiPayload,
    GlobalPayload,
)

SCHEMA_VERSION = "1"


def build_coingecko_schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    registrations: dict[str, type[BaseModel]] = {
        "coins_list": CoinsListPayload,
        "asset_platforms_list": AssetPlatformsListPayload,
        "global": GlobalPayload,
        "global_defi": GlobalDefiPayload,
        "coins_markets": CoinsMarketsPayload,
    }
    for entity, model in registrations.items():
        registry.register(
            source=COINGECKO_SOURCE,
            entity=entity,
            model=model,
            schema_name=f"{COINGECKO_SOURCE}_{entity}",
            schema_version=SCHEMA_VERSION,
        )
    return registry


def run_coingecko_source(
    *,
    entities: Sequence[str] | None = None,
    settings: Settings | None = None,
    extractor: CoinGeckoExtractor | None = None,
    writer: RawWriter | None = None,
) -> SourceRunSummary:
    started_at = datetime.now(UTC)
    settings = settings or get_settings()
    selected_entities = _normalize_entities(entities)

    owns_client = extractor is None
    client: RestClient | None = None
    if extractor is None:
        client = _build_rest_client(settings)
        extractor = CoinGeckoExtractor(
            client=client,
            markets_vs_currency=settings.coingecko_markets_vs_currency,
            markets_per_page=settings.coingecko_markets_per_page,
            markets_max_pages=settings.coingecko_markets_max_pages,
        )
    if writer is None:
        writer = RawWriter(
            schema_registry=build_coingecko_schema_registry(),
            loader=create_loader(settings),
            loader_batch_size=settings.loader_batch_size,
        )

    entity_summaries: list[EntityRunSummary] = []
    try:
        for entity in selected_entities:
            records = extractor.extract_entity(entity)
            result = writer.write(records)
            entity_summaries.append(
                EntityRunSummary.from_write_result(entity=entity, result=result)
            )
    finally:
        if owns_client and client is not None:
            client.close()

    return SourceRunSummary(
        source=COINGECKO_SOURCE,
        started_at=started_at,
        ended_at=datetime.now(UTC),
        entities=tuple(entity_summaries),
    )


def _build_rest_client(settings: Settings) -> RestClient:
    headers = {}
    if settings.coingecko_api_key:
        headers["x-cg-demo-api-key"] = settings.coingecko_api_key
    return RestClient(
        base_url=settings.coingecko_base_url,
        headers=headers,
        timeout_seconds=settings.coingecko_request_timeout_seconds,
        retry_max_attempts=settings.coingecko_retry_max_attempts,
    )


def _normalize_entities(entities: Iterable[str] | None) -> tuple[CoinGeckoEntity, ...]:
    if entities is None:
        return SUPPORTED_ENTITIES
    selected: list[CoinGeckoEntity] = []
    for entity in entities:
        if entity not in SUPPORTED_ENTITIES:
            msg = f"unsupported CoinGecko entity: {entity}"
            raise ConfigurationError(msg)
        selected.append(cast(CoinGeckoEntity, entity))
    return tuple(selected)

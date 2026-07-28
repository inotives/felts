"""Plain Python CCXT source runner."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from pydantic import BaseModel

from felts.config import Settings, get_settings
from felts.core.exceptions import ConfigurationError, ExtractionError
from felts.core.loaders import RawWriter, create_loader
from felts.core.schemas import SchemaRegistry
from felts.core.sources import EntityRunSummary, SourceRunSummary
from felts.sources.ccxt.constants import CCXT_SOURCE, SUPPORTED_ENTITIES, CcxtEntity
from felts.sources.ccxt.extractor import CcxtExtractor, load_ccxt_markets
from felts.sources.ccxt.schemas import OrderBookPayload, TickerPayload

SCHEMA_VERSION = "1"


def build_ccxt_schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    registrations: dict[str, type[BaseModel]] = {
        "ticker": TickerPayload,
        "order_book": OrderBookPayload,
    }
    for entity, model in registrations.items():
        registry.register(
            source=CCXT_SOURCE,
            entity=entity,
            model=model,
            schema_name=f"{CCXT_SOURCE}_{entity}",
            schema_version=SCHEMA_VERSION,
        )
    return registry


def run_ccxt_source(
    *,
    entities: Sequence[str] | None = None,
    settings: Settings | None = None,
    extractor: Any | None = None,
    writer: RawWriter | None = None,
) -> SourceRunSummary:
    started_at = datetime.now(UTC)
    settings = settings or get_settings()
    selected_entities = _normalize_entities(entities)

    owns_exchange = extractor is None
    exchange: Any | None = None
    if extractor is None:
        exchange = _build_exchange_client()
        extractor = CcxtExtractor(client=exchange, markets=load_ccxt_markets())
    if writer is None:
        writer = RawWriter(
            schema_registry=build_ccxt_schema_registry(),
            loader=create_loader(settings),
            loader_batch_size=settings.loader_batch_size,
        )

    entity_summaries: list[EntityRunSummary] = []
    try:
        for entity in selected_entities:
            try:
                records = extractor.extract_entity(entity)
            except ExtractionError:
                entity_summaries.append(_failed_entity_summary(entity))
                continue
            result = writer.write(records)
            entity_summaries.append(
                EntityRunSummary.from_write_result(entity=entity, result=result)
            )
    finally:
        if owns_exchange and exchange is not None:
            _close_exchange(exchange)

    return SourceRunSummary(
        source=CCXT_SOURCE,
        started_at=started_at,
        ended_at=datetime.now(UTC),
        entities=tuple(entity_summaries),
    )


def _build_exchange_client() -> Any:
    try:
        import ccxt  # type: ignore[import-untyped]
    except ModuleNotFoundError as exc:
        msg = "ccxt is required to run the CCXT source"
        raise ConfigurationError(msg) from exc
    return ccxt.binance({"enableRateLimit": True})


def _normalize_entities(entities: Sequence[str] | None) -> tuple[CcxtEntity, ...]:
    if entities is None:
        return SUPPORTED_ENTITIES
    selected: list[CcxtEntity] = []
    for entity in entities:
        if entity not in SUPPORTED_ENTITIES:
            msg = f"unsupported CCXT entity: {entity}"
            raise ConfigurationError(msg)
        selected.append(cast(CcxtEntity, entity))
    return tuple(selected)


def _failed_entity_summary(entity: CcxtEntity) -> EntityRunSummary:
    return EntityRunSummary(
        entity=entity,
        batch_id=uuid4().hex,
        extracted_count=0,
        inserted_count=0,
        skipped_duplicate_count=0,
        invalid_count=0,
        failed_count=1,
    )


def _close_exchange(exchange: Any) -> None:
    close = getattr(exchange, "close", None)
    if callable(close):
        close()

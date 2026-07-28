from collections.abc import Sequence
from typing import Any

import pytest
from pydantic import ValidationError

from felts.core.exceptions import ConfigurationError, ExtractionError
from felts.core.loaders import LoadResult, RawWriter
from felts.core.schemas import RawRecord
from felts.sources.ccxt.extractor import CcxtExtractor
from felts.sources.ccxt.runner import build_ccxt_schema_registry, run_ccxt_source


class MemoryLoader:
    def __init__(self) -> None:
        self.records: list[RawRecord] = []

    def write_records(self, records: Sequence[RawRecord]) -> LoadResult:
        self.records.extend(records)
        return LoadResult(inserted_count=len(records))


class FakeExtractor:
    def extract_entity(self, entity: str) -> list[Any]:
        if entity == "ticker":
            from datetime import UTC, datetime

            from felts.core.schemas import ExtractedRecord

            return [
                ExtractedRecord(
                    source="ccxt",
                    entity="ticker",
                    payload={
                        "exchange_id": "binance",
                        "symbol": "BTC/USDT",
                        "base_asset": "BTC",
                        "quote_asset": "USDT",
                        "timestamp": 1735689600000,
                        "datetime": "2025-01-01T00:00:00Z",
                        "bid": 100000.0,
                        "ask": 100010.0,
                        "last": 100005.0,
                        "open": 99000.0,
                        "high": 101000.0,
                        "low": 98000.0,
                        "close": 100005.0,
                        "base_volume": 12.5,
                        "quote_volume": 1250000.0,
                        "vwap": 100100.0,
                        "percentage": 1.5,
                        "raw_response": {"id": "kept"},
                    },
                    observed_at=datetime(2025, 1, 1, tzinfo=UTC),
                    source_record_id="ticker|binance|BTC/USDT|2025-01-01T00:00:00+00:00",
                )
            ]
        raise ExtractionError("binance blocked")


def test_ccxt_schema_registry_accepts_provider_extensions() -> None:
    registry = build_ccxt_schema_registry()
    registered = registry.get(source="ccxt", entity="ticker")

    assert registered is not None
    model = registered.model.model_validate(
        {
            "exchange_id": "binance",
            "symbol": "BTC/USDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "raw_response": {},
            "extra_field": "kept",
        }
    )
    assert model.model_extra == {"extra_field": "kept"}


def test_ccxt_schema_registry_rejects_missing_required_fields() -> None:
    registry = build_ccxt_schema_registry()
    registered = registry.get(source="ccxt", entity="order_book")

    assert registered is not None
    with pytest.raises(ValidationError):
        registered.model.model_validate({"symbol": "BTC/USDT"})


def test_run_ccxt_source_rejects_unknown_entity() -> None:
    with pytest.raises(ConfigurationError, match="unsupported CCXT entity"):
        run_ccxt_source(entities=["unknown"])


def test_run_ccxt_source_preserves_successful_entities_on_partial_failure() -> None:
    memory_loader = MemoryLoader()
    writer = RawWriter(
        schema_registry=build_ccxt_schema_registry(),
        loader=memory_loader,
    )

    summary = run_ccxt_source(
        entities=["ticker", "order_book"],
        extractor=FakeExtractor(),
        writer=writer,
    )

    assert summary.source == "ccxt"
    assert len(summary.entities) == 2
    assert summary.entities[0].entity == "ticker"
    assert summary.entities[0].inserted_count == 1
    assert summary.entities[1].entity == "order_book"
    assert summary.entities[1].failed_count == 1
    assert summary.failed_count == 1
    assert len(memory_loader.records) == 1


def test_run_ccxt_source_preserves_successful_entities_when_provider_failure_is_normalized() -> (
    None
):
    memory_loader = MemoryLoader()
    writer = RawWriter(
        schema_registry=build_ccxt_schema_registry(),
        loader=memory_loader,
    )
    extractor = CcxtExtractor(
        client=_provider_boom_client(),
        markets=_markets(),
    )

    summary = run_ccxt_source(
        entities=["ticker", "order_book"],
        extractor=extractor,
        writer=writer,
    )

    assert summary.entities[0].entity == "ticker"
    assert summary.entities[0].inserted_count == 1
    assert summary.entities[1].entity == "order_book"
    assert summary.entities[1].failed_count == 1
    assert summary.failed_count == 1
    assert len(memory_loader.records) == 1


def _provider_boom_client() -> Any:
    class ProviderBoomClient:
        def fetch_ticker(self, symbol: str) -> dict[str, object]:
            return {
                "timestamp": 1735689600000,
                "datetime": "2025-01-01T00:00:00Z",
                "bid": 100000.0,
                "ask": 100010.0,
                "last": 100005.0,
                "open": 99000.0,
                "high": 101000.0,
                "low": 98000.0,
                "close": 100005.0,
                "baseVolume": 12.5,
                "quoteVolume": 1250000.0,
                "vwap": 100100.0,
                "percentage": 1.5,
            }

        def fetch_order_book(self, symbol: str, limit: int | None = None) -> dict[str, object]:
            raise RuntimeError("provider boom")

    return ProviderBoomClient()


def _markets() -> tuple[Any, ...]:
    from felts.sources.ccxt.extractor import CcxtMarket

    return (
        CcxtMarket(
            exchange_id="binance",
            symbol="BTC/USDT",
            base_asset="BTC",
            quote_asset="USDT",
            order_book_limit=20,
            is_active=True,
        ),
    )

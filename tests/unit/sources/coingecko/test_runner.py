from collections.abc import Sequence
from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest_httpx import HTTPXMock

from felts.config import Settings
from felts.core.exceptions import ConfigurationError
from felts.core.extractors.rest import RestClient
from felts.core.loaders import LoadResult, RawWriter
from felts.core.schemas import RawRecord
from felts.sources.coingecko.extractor import CoinGeckoExtractor
from felts.sources.coingecko.runner import build_coingecko_schema_registry, run_coingecko_source


class MemoryLoader:
    def __init__(self) -> None:
        self.records: list[RawRecord] = []

    def write_records(self, records: Sequence[RawRecord]) -> LoadResult:
        self.records.extend(records)
        return LoadResult(inserted_count=len(records))


def test_coingecko_schema_registry_accepts_provider_extensions() -> None:
    registry = build_coingecko_schema_registry()
    registered = registry.get(source="coingecko", entity="coins_list")

    assert registered is not None
    model = registered.model.model_validate(
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "extra_field": "kept"}
    )
    assert model.model_extra == {"extra_field": "kept"}


def test_coingecko_schema_registry_rejects_missing_required_fields() -> None:
    registry = build_coingecko_schema_registry()
    registered = registry.get(source="coingecko", entity="coins_markets")

    assert registered is not None
    with pytest.raises(ValidationError):
        registered.model.model_validate({"symbol": "btc", "name": "Bitcoin"})


def test_coingecko_schema_registry_registers_coins_ohlc() -> None:
    registry = build_coingecko_schema_registry()
    registered = registry.get(source="coingecko", entity="coins_ohlc")

    assert registered is not None
    model = registered.model.model_validate(
        {
            "coin_id": "bitcoin",
            "vs_currency": "usd",
            "days": 30,
            "interval": "4h",
            "timestamp_ms": 1735689600000,
            "open": 100.0,
            "high": 110.0,
            "low": 90.0,
            "close": 105.0,
            "extra_field": "kept",
        }
    )
    assert model.model_extra == {"extra_field": "kept"}


def test_coingecko_schema_registry_registers_coins_market_chart() -> None:
    registry = build_coingecko_schema_registry()
    registered = registry.get(source="coingecko", entity="coins_market_chart")

    assert registered is not None
    model = registered.model.model_validate(
        {
            "coin_id": "bitcoin",
            "vs_currency": "usd",
            "days": 90,
            "interval": "daily",
            "timestamp_ms": 1735689600000,
            "price": 100.0,
            "market_cap": 200.0,
            "total_volume": 300.0,
            "extra_field": "kept",
        }
    )
    assert model.model_extra == {"extra_field": "kept"}


def test_run_coingecko_source_returns_entity_summary(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/coins/list",
        json=[
            {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
            {"symbol": "bad", "name": "Missing ID"},
        ],
    )
    memory_loader = MemoryLoader()
    writer = RawWriter(
        schema_registry=build_coingecko_schema_registry(),
        loader=memory_loader,
    )
    extractor = CoinGeckoExtractor(
        client=_test_rest_client(),
        markets_per_page=2,
        markets_max_pages=1,
    )

    summary = run_coingecko_source(
        entities=["coins_list"],
        settings=Settings(COINGECKO_BASE_URL="https://api.coingecko.test/api/v3"),
        extractor=extractor,
        writer=writer,
    )

    assert summary.source == "coingecko"
    assert summary.entities[0].entity == "coins_list"
    assert summary.entities[0].extracted_count == 2
    assert summary.entities[0].inserted_count == 2
    assert summary.entities[0].invalid_count == 1
    assert memory_loader.records[1].is_valid is False


def test_run_coingecko_source_rejects_unknown_entity() -> None:
    with pytest.raises(ConfigurationError, match="unsupported CoinGecko entity"):
        run_coingecko_source(entities=["unknown"])


def test_run_coingecko_source_supports_coins_ohlc(httpx_mock: HTTPXMock, tmp_path: Path) -> None:
    mappings_path = tmp_path / "asset_provider_mappings.csv"
    mappings_path.write_text(
        "\n".join(
            [
                "internal_asset_id,provider_source,provider_asset_id",
                "bitcoin,coingecko,bitcoin",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    httpx_mock.add_response(
        url=("https://api.coingecko.test/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=30"),
        json=[[1735689600000, 100.0, 110.0, 90.0, 105.0]],
    )
    memory_loader = MemoryLoader()
    writer = RawWriter(
        schema_registry=build_coingecko_schema_registry(),
        loader=memory_loader,
    )
    extractor = CoinGeckoExtractor(
        client=_test_rest_client(),
        asset_provider_mappings_path=mappings_path,
    )

    summary = run_coingecko_source(
        entities=["coins_ohlc"],
        settings=Settings(COINGECKO_BASE_URL="https://api.coingecko.test/api/v3"),
        extractor=extractor,
        writer=writer,
    )

    assert summary.entities[0].entity == "coins_ohlc"
    assert summary.entities[0].inserted_count == 1
    assert memory_loader.records[0].source_record_id == "bitcoin|usd|1735689600000"


def test_run_coingecko_source_supports_coins_market_chart(
    httpx_mock: HTTPXMock, tmp_path: Path
) -> None:
    mappings_path = tmp_path / "asset_provider_mappings.csv"
    mappings_path.write_text(
        "\n".join(
            [
                "internal_asset_id,provider_source,provider_asset_id",
                "bitcoin,coingecko,bitcoin",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    httpx_mock.add_response(
        url=(
            "https://api.coingecko.test/api/v3/coins/bitcoin/market_chart"
            "?vs_currency=usd&days=90&interval=daily"
        ),
        json={
            "prices": [[1735689600000, 100.0]],
            "market_caps": [[1735689600000, 200.0]],
            "total_volumes": [[1735689600000, 300.0]],
        },
    )
    memory_loader = MemoryLoader()
    writer = RawWriter(
        schema_registry=build_coingecko_schema_registry(),
        loader=memory_loader,
    )
    extractor = CoinGeckoExtractor(
        client=_test_rest_client(),
        asset_provider_mappings_path=mappings_path,
    )

    summary = run_coingecko_source(
        entities=["coins_market_chart"],
        settings=Settings(COINGECKO_BASE_URL="https://api.coingecko.test/api/v3"),
        extractor=extractor,
        writer=writer,
    )

    assert summary.entities[0].entity == "coins_market_chart"
    assert summary.entities[0].inserted_count == 1
    assert memory_loader.records[0].source_record_id == "bitcoin|usd|daily|1735689600000"


def _test_rest_client() -> RestClient:
    return RestClient(
        base_url="https://api.coingecko.test/api/v3",
        retry_backoff_seconds=0,
        sleep_fn=lambda _seconds: None,
    )

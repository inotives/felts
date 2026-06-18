from collections.abc import Sequence

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


def _test_rest_client() -> RestClient:
    return RestClient(
        base_url="https://api.coingecko.test/api/v3",
        retry_backoff_seconds=0,
        sleep_fn=lambda _seconds: None,
    )

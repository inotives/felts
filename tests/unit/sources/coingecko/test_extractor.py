from datetime import UTC, datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock

from felts.core.exceptions import ExtractionError
from felts.core.extractors.rest import RestClient
from felts.sources.coingecko.extractor import CoinGeckoExtractor


def _client() -> RestClient:
    return RestClient(
        base_url="https://api.coingecko.test/api/v3",
        retry_backoff_seconds=0,
        sleep_fn=lambda _seconds: None,
    )


def test_extracts_single_response_entities(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/coins/list",
        json=[{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}],
    )
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/asset_platforms",
        json=[{"id": "ethereum", "name": "Ethereum"}],
    )
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        json={
            "data": {
                "active_cryptocurrencies": 1,
                "markets": 2,
                "total_market_cap": {"usd": 100.0},
            }
        },
    )
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global/decentralized_finance_defi",
        json={
            "data": {
                "defi_market_cap": "10",
                "eth_market_cap": "20",
                "defi_to_eth_ratio": "0.5",
            }
        },
    )

    extractor = CoinGeckoExtractor(client=_client())

    assert extractor.extract_coins_list()[0].source_record_id == "bitcoin"
    assert extractor.extract_asset_platforms_list()[0].source_record_id == "ethereum"
    assert extractor.extract_global()[0].source_record_id == "global"
    assert extractor.extract_global_defi()[0].source_record_id == "global_defi"


def test_extracts_coins_markets_with_pagination_and_observed_at(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        url=("https://api.coingecko.test/api/v3/coins/markets?vs_currency=usd&per_page=2&page=1"),
        json=[
            {
                "id": "bitcoin",
                "symbol": "btc",
                "name": "Bitcoin",
                "current_price": 100,
                "last_updated": "2026-01-01T00:00:00Z",
            },
            {
                "id": "ethereum",
                "symbol": "eth",
                "name": "Ethereum",
                "current_price": 10,
                "last_updated": "2026-01-01T00:01:00Z",
            },
        ],
    )
    httpx_mock.add_response(
        url=("https://api.coingecko.test/api/v3/coins/markets?vs_currency=usd&per_page=2&page=2"),
        json=[
            {
                "id": "solana",
                "symbol": "sol",
                "name": "Solana",
                "current_price": 5,
                "last_updated": "2026-01-01T00:02:00Z",
            }
        ],
    )

    extractor = CoinGeckoExtractor(client=_client(), markets_per_page=2, markets_max_pages=5)
    records = extractor.extract_coins_markets()

    assert [record.source_record_id for record in records] == ["bitcoin", "ethereum", "solana"]
    assert records[0].observed_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_rest_client_retries_retryable_status(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        status_code=429,
        headers={"Retry-After": "0"},
        json={"status": "limited"},
    )
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        json={"data": {"active_cryptocurrencies": 1, "markets": 1, "total_market_cap": {"usd": 1}}},
    )

    data = _client().get_json("/global")

    assert isinstance(data, dict)
    assert "data" in data


def test_malformed_top_level_shape_fails(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        json={"unexpected": {}},
    )

    extractor = CoinGeckoExtractor(client=_client())

    with pytest.raises(ExtractionError, match="data object"):
        extractor.extract_global()


def test_http_failure_after_retries_raises_extraction_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        status_code=500,
        json={"error": "down"},
    )
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        status_code=500,
        json={"error": "still down"},
    )
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        status_code=500,
        json={"error": "done"},
    )

    with pytest.raises(ExtractionError, match="after 3 attempt"):
        _client().get_json("/global")


def test_non_json_response_raises_extraction_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        content=b"not-json",
        headers={"content-type": "text/plain"},
    )

    with pytest.raises(ExtractionError, match="after 3 attempt"):
        _client().get_json("/global")


def test_network_error_is_retried(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError("temporary"))
    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/global",
        json={"data": {"active_cryptocurrencies": 1, "markets": 1, "total_market_cap": {"usd": 1}}},
    )

    assert isinstance(_client().get_json("/global"), dict)

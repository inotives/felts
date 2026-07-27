from datetime import UTC, datetime
from pathlib import Path

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


def test_extracts_coins_ohlc_from_seed_mappings_with_duplicate_safe_identity(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    mappings_path = tmp_path / "asset_provider_mappings.csv"
    mappings_path.write_text(
        "\n".join(
            [
                "internal_asset_id,provider_source,provider_asset_id",
                "bitcoin,coingecko,bitcoin",
                "wrapped-bitcoin,coingecko,bitcoin",
                "ethereum,coingecko,ethereum",
                "apple,alphavantage,AAPL",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    httpx_mock.add_response(
        url=(
            "https://api.coingecko.test/api/v3/coins/bitcoin/ohlc"
            "?vs_currency=usd&days=90&interval=daily"
        ),
        json=[[1735689600000, 100.0, 110.0, 90.0, 105.0]],
    )
    httpx_mock.add_response(
        url=(
            "https://api.coingecko.test/api/v3/coins/ethereum/ohlc"
            "?vs_currency=usd&days=90&interval=daily"
        ),
        json=[[1735776000000, 10.0, 11.0, 9.0, 10.5]],
    )

    extractor = CoinGeckoExtractor(
        client=_client(),
        asset_provider_mappings_path=mappings_path,
    )

    records = extractor.extract_coins_ohlc()

    assert [record.payload["coin_id"] for record in records] == ["bitcoin", "ethereum"]
    assert [record.source_record_id for record in records] == [
        "bitcoin|usd|1735689600000",
        "ethereum|usd|1735776000000",
    ]
    assert records[0].payload == {
        "coin_id": "bitcoin",
        "vs_currency": "usd",
        "days": 90,
        "interval": "daily",
        "timestamp_ms": 1735689600000,
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
    }
    assert records[0].observed_at == datetime(2025, 1, 1, tzinfo=UTC)
    requests = httpx_mock.get_requests()
    assert [str(request.url.path) for request in requests] == [
        "/api/v3/coins/bitcoin/ohlc",
        "/api/v3/coins/ethereum/ohlc",
    ]
    assert requests[0].url.params["vs_currency"] == "usd"
    assert requests[0].url.params["days"] == "90"
    assert requests[0].url.params["interval"] == "daily"


def test_extracts_coins_market_chart_from_seed_mappings_with_stable_identity(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    mappings_path = tmp_path / "asset_provider_mappings.csv"
    mappings_path.write_text(
        "\n".join(
            [
                "internal_asset_id,provider_source,provider_asset_id",
                "bitcoin,coingecko,bitcoin",
                "wrapped-bitcoin,coingecko,bitcoin",
                "ethereum,coingecko,ethereum",
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
    httpx_mock.add_response(
        url=(
            "https://api.coingecko.test/api/v3/coins/ethereum/market_chart"
            "?vs_currency=usd&days=90&interval=daily"
        ),
        json={
            "prices": [[1735776000000, 10.0]],
            "market_caps": [[1735776000000, 20.0]],
            "total_volumes": [[1735776000000, 30.0]],
        },
    )

    extractor = CoinGeckoExtractor(
        client=_client(),
        asset_provider_mappings_path=mappings_path,
    )

    records = extractor.extract_coins_market_chart()

    assert [record.payload["coin_id"] for record in records] == ["bitcoin", "ethereum"]
    assert [record.source_record_id for record in records] == [
        "bitcoin|usd|daily|1735689600000",
        "ethereum|usd|daily|1735776000000",
    ]
    assert records[0].payload == {
        "coin_id": "bitcoin",
        "vs_currency": "usd",
        "days": 90,
        "interval": "daily",
        "timestamp_ms": 1735689600000,
        "price": 100.0,
        "market_cap": 200.0,
        "total_volume": 300.0,
    }
    assert records[0].observed_at == datetime(2025, 1, 1, tzinfo=UTC)
    requests = httpx_mock.get_requests()
    assert [str(request.url.path) for request in requests] == [
        "/api/v3/coins/bitcoin/market_chart",
        "/api/v3/coins/ethereum/market_chart",
    ]
    assert requests[0].url.params["vs_currency"] == "usd"
    assert requests[0].url.params["days"] == "90"
    assert requests[0].url.params["interval"] == "daily"


@pytest.mark.parametrize(
    "response_json",
    [
        {"unexpected": []},
        [[1735689600000, 100.0, 110.0, 90.0]],
        [[1735689600000, 100.0, 110.0, 90.0, "bad"]],
    ],
)
def test_malformed_coins_ohlc_shape_fails(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
    response_json: object,
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
            "https://api.coingecko.test/api/v3/coins/bitcoin/ohlc"
            "?vs_currency=usd&days=90&interval=daily"
        ),
        json=response_json,
    )

    extractor = CoinGeckoExtractor(
        client=_client(),
        asset_provider_mappings_path=mappings_path,
    )

    with pytest.raises(ExtractionError, match="coins_ohlc"):
        extractor.extract_coins_ohlc()


@pytest.mark.parametrize(
    "response_json,error_match",
    [
        ([], "response must be an object"),
        ({"prices": "bad", "market_caps": [], "total_volumes": []}, "prices must be a list"),
        (
            {"prices": [[1735689600000]], "market_caps": [], "total_volumes": []},
            "rows must be two-item arrays",
        ),
        (
            {
                "prices": [[1735689600000, 1.0]],
                "market_caps": [[1735776000000, 2.0]],
                "total_volumes": [[1735689600000, 3.0]],
            },
            "must share the same timestamps",
        ),
    ],
)
def test_malformed_coins_market_chart_shape_fails(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
    response_json: object,
    error_match: str,
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
        json=response_json,
    )

    extractor = CoinGeckoExtractor(
        client=_client(),
        asset_provider_mappings_path=mappings_path,
    )

    with pytest.raises(ExtractionError, match=error_match):
        extractor.extract_coins_market_chart()


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

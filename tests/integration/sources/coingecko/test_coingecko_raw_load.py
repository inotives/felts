import psycopg
import pytest
from pytest_httpx import HTTPXMock

from felts.config import Settings
from felts.core.extractors.rest import RestClient
from felts.core.loaders import RawWriter, create_loader, postgres_loader_config_from_settings
from felts.sources.coingecko.extractor import CoinGeckoExtractor
from felts.sources.coingecko.runner import build_coingecko_schema_registry, run_coingecko_source


def _postgres_available(conninfo: str) -> bool:
    try:
        with psycopg.connect(conninfo, connect_timeout=2):
            return True
    except psycopg.OperationalError:
        return False


def test_mocked_coingecko_source_loads_into_raw_postgres(httpx_mock: HTTPXMock) -> None:
    settings = Settings(COINGECKO_BASE_URL="https://api.coingecko.test/api/v3")
    config = postgres_loader_config_from_settings(settings)
    if not _postgres_available(config.conninfo):
        pytest.skip("local Postgres is not available; run `make db-up`")

    httpx_mock.add_response(
        url="https://api.coingecko.test/api/v3/coins/list",
        json=[{"id": "phase-02-bitcoin", "symbol": "btc", "name": "Bitcoin"}],
    )

    loader = create_loader(settings)
    writer = RawWriter(
        schema_registry=build_coingecko_schema_registry(),
        loader=loader,
        loader_batch_size=settings.loader_batch_size,
    )
    extractor = CoinGeckoExtractor(client=_test_rest_client())

    summary = run_coingecko_source(
        entities=["coins_list"],
        settings=settings,
        extractor=extractor,
        writer=writer,
    )

    assert summary.entities[0].extracted_count == 1
    assert summary.entities[0].inserted_count in {0, 1}

    with psycopg.connect(config.conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select to_regclass('coingecko.raw_coins_list')")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "coingecko.raw_coins_list"


def _test_rest_client() -> RestClient:
    return RestClient(
        base_url="https://api.coingecko.test/api/v3",
        retry_backoff_seconds=0,
        sleep_fn=lambda _seconds: None,
    )

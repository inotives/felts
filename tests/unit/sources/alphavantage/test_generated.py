import pytest
from pydantic import ValidationError

from felts.core.exceptions import ExtractionError
from felts.sources.alphavantage.constants import (
    ALPHAVANTAGE_BASE_URL,
    ENDPOINTS,
)
from felts.sources.alphavantage.deployments import build_source_deployment_specs
from felts.sources.alphavantage.schemas import TimeSeriesDailyPayload


def test_generated_source_defaults() -> None:
    assert ALPHAVANTAGE_BASE_URL == "https://www.alphavantage.co"
    assert [spec.entity for spec in build_source_deployment_specs()] == list(ENDPOINTS)


def test_time_series_schema_requires_identity_fields() -> None:
    with pytest.raises(ValidationError):
        TimeSeriesDailyPayload.model_validate({"symbol": "AAPL"})


# scaffold: entity-tests:start
def test_time_series_daily_endpoint_shape() -> None:
    from unittest.mock import Mock

    from felts.sources.alphavantage.extractor import AlphavantageExtractor

    client = Mock()
    client.get_json.return_value = {"Time Series (Daily)": {"record-key": {"value": 1}}}
    records = AlphavantageExtractor(client=client, api_key="test-key").extract_entity(
        "time_series_daily",
        runtime_params={"symbol": ["symbol-value"]},
    )

    assert len(records) == 1
    assert records[0].payload == {
        "symbol": "symbol-value",
        "trading_date": "record-key",
        "value": 1,
    }


def test_time_series_daily_adds_api_key_and_spaces_symbol_requests() -> None:
    from unittest.mock import Mock

    from felts.sources.alphavantage.extractor import AlphavantageExtractor

    client = Mock()
    client.get_json.return_value = {"Time Series (Daily)": {"2026-06-24": {"4. close": "100"}}}
    sleeps: list[float] = []

    records = AlphavantageExtractor(
        client=client,
        api_key="test-key",
        sleep_fn=sleeps.append,
    ).extract_entity(
        "time_series_daily",
        runtime_params={"symbol": ["AAPL", "NVDA"]},
    )

    assert len(records) == 2
    assert sleeps == [2.0]
    assert client.get_json.call_args_list[0].kwargs["params"]["apikey"] == "test-key"
    assert client.get_json.call_args_list[1].kwargs["params"]["symbol"] == "NVDA"


@pytest.mark.parametrize("key", ["Error Message", "Information", "Note"])
def test_alpha_vantage_error_envelopes_fail(key: str) -> None:
    from unittest.mock import Mock

    from felts.sources.alphavantage.extractor import AlphavantageExtractor

    client = Mock()
    client.get_json.return_value = {key: "provider message"}

    with pytest.raises(ExtractionError, match=key):
        AlphavantageExtractor(client=client, api_key="test-key").extract_entity(
            "time_series_daily",
            runtime_params={"symbol": ["AAPL"]},
        )


# scaffold: entity-tests:end

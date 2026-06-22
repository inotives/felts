from pathlib import Path

import pytest

from felts.core.exceptions import ConfigurationError, ExtractionError
from felts.core.extractors.csv import CsvFileExtractor, validate_headers
from felts.sources.csv_import.contracts import load_csv_contracts


def test_ohlcv_extractor_adds_felts_metadata() -> None:
    contract = load_csv_contracts()["ohlcv"]
    input_file = Path("tests/fixtures/csv_import/crypto-ohlcv-bitcoin-20260528.csv")

    records = list(CsvFileExtractor(contract=contract, input_uri=str(input_file)).extract())

    assert records[0].source == "csv_import"
    assert records[0].entity == "ohlcv"
    assert records[0].source_record_id == "bitcoin|2026-05-28T00:00:00Z|2"
    assert records[0].payload["_felts"]["identity"]["asset_slug"] == "bitcoin"


def test_fred_extractor_uses_value_column_header_as_series_id() -> None:
    contract = load_csv_contracts()["fred_series"]

    records = list(
        CsvFileExtractor(
            contract=contract,
            input_uri="tests/fixtures/csv_import/fred_series.csv",
        ).extract()
    )

    assert records[0].source_record_id == "CORESTICKM159SFRBATL|2026-05-01"
    assert records[0].payload["_felts"]["identity"]["series_id"] == "CORESTICKM159SFRBATL"


def test_csv_rejects_unsupported_uri_scheme() -> None:
    contract = load_csv_contracts()["ohlcv"]

    with pytest.raises(ConfigurationError, match="unsupported CSV input URI scheme"):
        list(
            CsvFileExtractor(contract=contract, input_uri="https://example.test/file.csv").extract()
        )


def test_strict_header_validation_rejects_extra_headers() -> None:
    contract = load_csv_contracts()["ohlcv"]

    with pytest.raises(ExtractionError, match="unsupported headers"):
        validate_headers(contract=contract, headers=(*contract.required_headers, "extra"))
